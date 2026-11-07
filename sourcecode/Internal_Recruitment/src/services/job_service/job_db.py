"""
job_db.py - Database Layer for Job Posting & Lifecycle Microservice
Owns its own isolated database: jobs.db (Database-per-Service pattern).
Calculates real-time statuses (OPEN, CLOSING_SOON, CLOSED) based on deadlines.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS jobs")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        level TEXT NOT NULL,
        salary_range TEXT NOT NULL,
        location TEXT NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT NOT NULL,
        status TEXT DEFAULT 'OPEN',
        deadline_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    seed_jobs(conn)
    conn.close()


def seed_jobs(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs")
    if c.fetchone()[0] == 0:
        today = datetime.now()
        # Create deadlines: +14 days (OPEN), +2 days (CLOSING_SOON), -1 day (CLOSED)
        d_open1 = (today + timedelta(days=15)).strftime("%Y-%m-%d")
        d_open2 = (today + timedelta(days=20)).strftime("%Y-%m-%d")
        d_closing = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        d_closed = (today - timedelta(days=3)).strftime("%Y-%m-%d")

        sample_jobs = [
            (
                "JOB-001",
                "Senior Data Engineer (Nội Bộ)",
                "Data & Analytics",
                "Senior",
                "35.000.000 - 45.000.000 VNĐ",
                "Hà Nội / Hybrid",
                "Xây dựng hệ thống Data Pipeline, quản lý Data Warehouse BigQuery và tối ưu hóa ETL nội bộ công ty.",
                "Python, SQL, Spark, BigQuery, Airflow",
                "OPEN",
                d_open1
            ),
            (
                "JOB-002",
                "Technical Product Manager (Chuyển Nhánh)",
                "Product Management",
                "Lead / Senior",
                "40.000.000 - 50.000.000 VNĐ",
                "TP. Hồ Chí Minh",
                "Dẫn dắt sản phẩm Cổng thanh toán và ứng dụng khách hàng. Phù hợp cho Kỹ sư muốn chuyển hướng Product.",
                "Product Roadmap, Agile/Scrum, API Design, Data Analysis",
                "CLOSING_SOON",
                d_closing
            ),
            (
                "JOB-003",
                "Senior UI/UX Designer",
                "Design & Creative",
                "Senior",
                "28.000.000 - 38.000.000 VNĐ",
                "Hà Nội / Remote",
                "Thiết kế Design System cho toàn bộ hệ sinh thái sản phẩm số nội bộ và khách hàng của công ty.",
                "Figma, Design System, UX Research, Prototyping",
                "OPEN",
                d_open2
            ),
            (
                "JOB-004",
                "DevOps / Cloud Specialist",
                "Infrastructure & Cloud",
                "Mid / Senior",
                "30.000.000 - 42.000.000 VNĐ",
                "TP. Hồ Chí Minh",
                "Vận hành hạ tầng Kubernetes, CI/CD pipeline và tối ưu hóa chi phí đám mây AWS.",
                "Kubernetes, Docker, Terraform, AWS, CI/CD",
                "CLOSED",
                d_closed
            )
        ]

        for j in sample_jobs:
            c.execute("""
            INSERT INTO jobs (job_id, title, department, level, salary_range, location, description, required_skills, status, deadline_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, j)
        conn.commit()


def compute_realtime_status(row):
    """Calculates status based on deadline comparison with current time."""
    job = dict(row)
    manual_status = job.get("status", "OPEN")

    if manual_status in ["CLOSED", "FILLED"]:
        job["computed_status"] = manual_status
        job["remaining_days"] = 0
        job["remaining_hours"] = 0
        return job

    try:
        deadline = datetime.strptime(job["deadline_date"], "%Y-%m-%d") + timedelta(hours=23, minutes=59, seconds=59)
        now = datetime.now()
        diff = deadline - now

        if diff.total_seconds() <= 0:
            job["computed_status"] = "CLOSED"
            job["remaining_days"] = 0
            job["remaining_hours"] = 0
        elif diff.total_seconds() <= 72 * 3600:  # <= 72 hours
            job["computed_status"] = "CLOSING_SOON"
            job["remaining_days"] = max(0, diff.days)
            job["remaining_hours"] = int(diff.total_seconds() // 3600)
        else:
            job["computed_status"] = "OPEN"
            job["remaining_days"] = diff.days
            job["remaining_hours"] = int(diff.total_seconds() // 3600)
    except Exception:
        job["computed_status"] = manual_status
        job["remaining_days"] = 0
        job["remaining_hours"] = 0

    return job


def get_all_jobs(keyword="", department="", level="", only_active=False):
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if department and department != "ALL":
        query += " AND department = ?"
        params.append(department)

    if level and level != "ALL":
        query += " AND level = ?"
        params.append(level)

    if keyword:
        query += " AND (title LIKE ? OR description LIKE ? OR required_skills LIKE ?)"
        term = f"%{keyword}%"
        params.extend([term, term, term])

    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    result = [compute_realtime_status(r) for r in rows]
    if only_active:
        result = [j for j in result if j["computed_status"] in ["OPEN", "CLOSING_SOON"]]

    return result


def get_job_by_id(job_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = c.fetchone()
    conn.close()
    return compute_realtime_status(row) if row else None


def create_job(data):
    import uuid
    job_id = f"JOB-{uuid.uuid4().hex[:4].upper()}"
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO jobs (job_id, title, department, level, salary_range, location, description, required_skills, status, deadline_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
    """, (
        job_id,
        data.get("title", "Vị trí mới"),
        data.get("department", "Engineering"),
        data.get("level", "Mid"),
        data.get("salary_range", "Thương lượng"),
        data.get("location", "Hà Nội"),
        data.get("description", ""),
        data.get("required_skills", ""),
        data.get("deadline_date", (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"))
    ))
    conn.commit()
    conn.close()
    return get_job_by_id(job_id)


def extend_job_deadline(job_id, new_deadline):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE jobs 
    SET deadline_date = ?, status = 'OPEN', updated_at = CURRENT_TIMESTAMP
    WHERE job_id = ?
    """, (new_deadline, job_id))
    conn.commit()
    conn.close()
    return get_job_by_id(job_id)


def close_job(job_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE jobs SET status = 'CLOSED', updated_at = CURRENT_TIMESTAMP WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()
    return get_job_by_id(job_id)


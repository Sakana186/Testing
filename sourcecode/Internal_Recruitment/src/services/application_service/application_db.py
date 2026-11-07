"""
application_db.py - Database Layer for Application & Kanban Pipeline Service
Owns its own isolated database: applications.db (Database-per-Service pattern).
Manages application submissions, active limit checks, and Kanban pipeline statuses.
"""

import sqlite3
import uuid
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "applications.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS applications")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        application_id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        job_title TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        employee_name TEXT NOT NULL,
        current_department TEXT NOT NULL,
        cover_letter TEXT,
        resume_file TEXT,
        status TEXT DEFAULT 'APPLIED',
        interview_score INTEGER DEFAULT 0,
        hr_notes TEXT DEFAULT '',
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    seed_applications(conn)
    conn.close()


def seed_applications(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM applications")
    if c.fetchone()[0] == 0:
        sample_apps = [
            (
                "APP-20260918-0001",
                "JOB-001",
                "Senior Data Engineer (Nội Bộ)",
                "EMP-103",
                "Lê Hoàng Nam",
                "Quality Assurance",
                "Tôi đã có kinh nghiệm viết Python automation test và muốn chuyển sang mảng Data Engineering.",
                "CV_LeHoangNam_Data.pdf",
                "APPLIED",
                0,
                "Hồ sơ mới nộp, chờ HR sàng lọc."
            ),
            (
                "APP-20260918-0002",
                "JOB-002",
                "Technical Product Manager (Chuyển Nhánh)",
                "EMP-101",
                "Nguyễn Văn An",
                "Software Engineering",
                "Là Senior Backend Developer với 2 năm kinh nghiệm, tôi am hiểu sâu về kiến trúc hệ thống và muốn phát triển lên vai trò Technical PM.",
                "Internal_Profile_EMP101.pdf",
                "HR_SCREENING",
                4,
                "CV ấn tượng, kiến thức kỹ thuật rất vững. Đang xếp lịch phỏng vấn với Head of Product."
            ),
            (
                "APP-20260918-0003",
                "JOB-003",
                "Senior UI/UX Designer",
                "EMP-104",
                "Phạm Hương Giang",
                "UI/UX Design",
                "Mong muốn đảm nhận vai trò thiết kế chính cho dự án Mobile App mới.",
                "Portfolio_GiangPham_2026.pdf",
                "INTERVIEW",
                5,
                "Đã phỏng vấn vòng 1 ngày hôm qua, portfolio xuất sắc. Chờ duyệt Offer."
            )
        ]
        for a in sample_apps:
            c.execute("""
            INSERT INTO applications (application_id, job_id, job_title, employee_id, employee_name, current_department, cover_letter, resume_file, status, interview_score, hr_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, a)
        conn.commit()


def get_all_applications():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM applications ORDER BY submitted_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_applications_by_employee(employee_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE employee_id = ? ORDER BY submitted_at DESC", (employee_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_active_count(employee_id):
    """Counts applications that are currently active (APPLIED, HR_SCREENING, INTERVIEW)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT COUNT(*) FROM applications 
    WHERE employee_id = ? AND status IN ('APPLIED', 'HR_SCREENING', 'INTERVIEW')
    """, (employee_id,))
    cnt = c.fetchone()[0]
    conn.close()
    return cnt


def has_applied_for_job(job_id, employee_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT COUNT(*) FROM applications 
    WHERE job_id = ? AND employee_id = ? AND status NOT IN ('REJECTED')
    """, (job_id, employee_id))
    cnt = c.fetchone()[0]
    conn.close()
    return cnt > 0


def create_application_record(job_id, job_title, employee_id, employee_name, department, cover_letter, resume_file):
    today_str = datetime.now().strftime("%Y%m%d")
    short_id = uuid.uuid4().hex[:4].upper()
    app_id = f"APP-{today_str}-{short_id}"

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO applications (application_id, job_id, job_title, employee_id, employee_name, current_department, cover_letter, resume_file, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'APPLIED')
    """, (app_id, job_id, job_title, employee_id, employee_name, department, cover_letter, resume_file))
    conn.commit()
    conn.close()
    return app_id


def update_status(application_id, new_status, notes="", score=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE applications 
    SET status = ?, 
        hr_notes = CASE WHEN ? != '' THEN ? ELSE hr_notes END,
        interview_score = CASE WHEN ? IS NOT NULL THEN ? ELSE interview_score END,
        updated_at = CURRENT_TIMESTAMP
    WHERE application_id = ?
    """, (new_status, notes, notes, score, score, application_id))
    conn.commit()

    c.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


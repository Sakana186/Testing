"""
employee_db.py - Database Layer for Employee Profile & Talent Service
Owns its own isolated database: employees.db (Database-per-Service pattern).
Manages employee profiles, seniority, and talent mobility eligibility checks.
"""

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employees.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS employees")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        current_department TEXT NOT NULL,
        current_title TEXT NOT NULL,
        seniority_months INTEGER NOT NULL,
        skills_json TEXT NOT NULL,
        is_eligible INTEGER DEFAULT 1
    )
    """)
    conn.commit()
    seed_employees(conn)
    conn.close()


def seed_employees(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        sample_employees = [
            (
                "EMP-101",
                "Nguyễn Văn An",
                "an.nguyen@company.internal",
                "Công nghệ thông tin",
                "Senior Backend Developer",
                18,
                json.dumps(["Python", "SQL", "Data Pipeline", "Docker", "API Design"]),
                1
            ),
            (
                "EMP-102",
                "Trần Thị Bích (Nhân sự mới)",
                "bich.tran@company.internal",
                "Tài chính - Kế toán",
                "Junior Accountant",
                4,  # Under 6 months! Used to test eligibility boundary
                json.dumps(["Accounting", "Excel", "Tax"]),
                1
            ),
            (
                "EMP-103",
                "Lê Hoàng Nam",
                "nam.le@company.internal",
                "Kinh doanh & Tiếp thị",
                "Marketing Specialist",
                24,
                json.dumps(["Growth", "Digital Marketing", "SEO", "Analytics"]),
                1
            ),
            (
                "EMP-104",
                "Phạm Minh Đức (Kỷ luật Cảnh cáo)",
                "duc.pham@company.internal",
                "Vận hành & Hậu cần",
                "Operations Associate",
                8,
                json.dumps(["Logistics", "Inventory", "ERP"]),
                0  # Disciplinary action! Used to test disciplinary boundary
            )
        ]
        for e in sample_employees:
            c.execute("""
            INSERT INTO employees (employee_id, name, email, current_department, current_title, seniority_months, skills_json, is_eligible)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, e)
        conn.commit()


def _format_emp_dict(row):
    if not row:
        return None
    emp = dict(row)
    emp["skills"] = json.loads(emp["skills_json"])
    emp["months_at_company"] = emp["seniority_months"]
    emp["disciplinary_status"] = "CLEAR" if emp["is_eligible"] == 1 else "WARNING"
    return emp


def get_employee(employee_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
    row = c.fetchone()
    conn.close()
    return _format_emp_dict(row)


def get_all_employees():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM employees ORDER BY employee_id")
    rows = [_format_emp_dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def check_eligibility(employee_id):
    emp = get_employee(employee_id)
    if not emp:
        return False, "Không tìm thấy thông tin nhân viên trên hệ thống nhân sự", None

    if emp["is_eligible"] == 0 or emp["disciplinary_status"] != "CLEAR":
        return False, "Nhân viên đang trong diện kỷ luật cảnh cáo hoặc tạm dừng chuyển đổi", emp

    if emp["seniority_months"] < 6:
        return False, f"Chưa đủ điều kiện thâm niên tối thiểu 6 tháng tại vị trí hiện tại (Hiện tại: {emp['seniority_months']} tháng)", emp

    return True, "Nhân viên đủ điều kiện tham gia tuyển dụng và điều chuyển nội bộ", emp


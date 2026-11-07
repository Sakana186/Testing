"""
notification_db.py - Database Layer for Notification & Talent Alert Service
Owns its own isolated database: notifications.db (Database-per-Service pattern).
Stores real-time alerts, status updates, and interview invites.
"""

import sqlite3
import uuid
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notifications.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS notifications")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    seed_notifications(conn)
    conn.close()


def seed_notifications(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications")
    if c.fetchone()[0] == 0:
        sample_notis = [
            (
                "NOTI-001",
                "EMP-101",
                "🎯 Gợi ý việc làm nội bộ phù hợp kỹ năng của bạn",
                "Bộ phận Data & Analytics vừa mở tin tuyển dụng 'Senior Data Engineer'. Hồ sơ kỹ năng Python & SQL của bạn có độ tương thích cao (92%)!",
                "JOB_MATCH",
                0
            ),
            (
                "NOTI-002",
                "EMP-101",
                "📋 Chào mừng bạn đến với Cổng Tuyển Dụng Nội Bộ",
                "Bạn có thể tra cứu các cơ hội nghề nghiệp mới nhất và ứng tuyển bảo mật 100% với quản lý trực tiếp.",
                "SYSTEM",
                1
            )
        ]
        for n in sample_notis:
            c.execute("""
            INSERT INTO notifications (notification_id, employee_id, title, message, type, is_read)
            VALUES (?, ?, ?, ?, ?, ?)
            """, n)
        conn.commit()


def create_notification(employee_id, title, message, noti_type="STATUS_UPDATE"):
    noti_id = f"NOTI-{uuid.uuid4().hex[:6].upper()}"
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO notifications (notification_id, employee_id, title, message, type, is_read)
    VALUES (?, ?, ?, ?, ?, 0)
    """, (noti_id, employee_id, title, message, noti_type))
    conn.commit()
    conn.close()
    return noti_id


def get_notifications(employee_id="EMP-101"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM notifications 
    WHERE employee_id = ? 
    ORDER BY created_at DESC
    """, (employee_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def mark_as_read(employee_id, noti_id=None):
    conn = get_connection()
    c = conn.cursor()
    if noti_id:
        c.execute("UPDATE notifications SET is_read = 1 WHERE employee_id = ? AND notification_id = ?", (employee_id, noti_id))
    else:
        c.execute("UPDATE notifications SET is_read = 1 WHERE employee_id = ?", (employee_id,))
    conn.commit()
    conn.close()


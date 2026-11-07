"""
customer_db.py - Database Layer for Customer & Loyalty Microservice
Owns its own isolated database: customers.db (Database-per-Service pattern).
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "customers.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS customers")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        wallet_balance REAL DEFAULT 2500000.0,
        loyalty_tier TEXT DEFAULT 'GOLD_VIP',
        credit_score INTEGER DEFAULT 780,
        pay_later_limit REAL DEFAULT 500000.0,
        pay_later_used REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    seed_customers(conn)
    conn.close()


def seed_customers(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customers WHERE user_id = 'USER_001'")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO customers (user_id, name, phone, wallet_balance, loyalty_tier, credit_score, pay_later_limit, pay_later_used)
        VALUES ('USER_001', 'Nguyễn Văn An', '0912345678', 2500000.0, 'GOLD_VIP', 780, 500000.0, 0.0)
        """)
        conn.commit()


def get_customer(user_id="USER_001"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def deduct_balance(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT wallet_balance FROM customers WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Khách hàng không tồn tại", 0.0

    current_balance = row["wallet_balance"]
    if current_balance < amount:
        conn.close()
        return False, f"Số dư không đủ ({current_balance:,.0f}đ < {amount:,.0f}đ)", current_balance

    new_balance = current_balance - amount
    c.execute("UPDATE customers SET wallet_balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()
    return True, "Trừ tiền thành công", new_balance


def update_pay_later(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET pay_later_used = pay_later_used + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


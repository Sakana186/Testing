"""
pos_db.py - Database Layer for POS & Order Microservice
Owns its own isolated database: pos.db (Database-per-Service pattern).
"""

import sqlite3
import json
import uuid
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pos.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS parked_orders")
    c.execute("DROP TABLE IF EXISTS products")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. Products Catalog
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        barcode TEXT UNIQUE NOT NULL,
        price REAL NOT NULL,
        unit TEXT NOT NULL,
        category TEXT NOT NULL
    )
    """)

    # 2. Parked Orders (Suspended carts)
    c.execute("""
    CREATE TABLE IF NOT EXISTS parked_orders (
        park_id TEXT PRIMARY KEY,
        store_id TEXT NOT NULL,
        terminal_id TEXT NOT NULL,
        cashier_id TEXT NOT NULL,
        customer_id TEXT,
        total_amount REAL NOT NULL,
        order_items_json TEXT NOT NULL,
        status TEXT DEFAULT 'SUSPENDED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )
    """)

    conn.commit()
    seed_products(conn)
    conn.close()


def seed_products(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ("P001", "Sữa tươi tiệt trùng Vinamilk 1L", "89346731001", 38000, "Hộp", "Sữa & Chế phẩm"),
            ("P002", "Thịt thăn bò Úc tươi 500g", "89346731002", 185000, "Khay", "Thịt tươi sống"),
            ("P003", "Bánh mì hoa cúc Harrys Pháp", "89346731003", 125000, "Gói", "Bánh mì"),
            ("P004", "Nước ép cam Vfresh 1L", "89346731004", 45000, "Hộp", "Đồ uống"),
            ("P005", "Gạo lứt đỏ ST25 hữu cơ 2kg", "89346731005", 95000, "Túi", "Lương thực"),
            ("P006", "Dầu oliu nguyên chất Olivo 500ml", "89346731006", 160000, "Chai", "Gia vị"),
            ("P007", "Rau chân vịt Đà Lạt 300g", "89346731007", 25000, "Gói", "Rau củ"),
            ("P008", "Cá hồi phi lê Na Uy tươi 300g", "89346731008", 220000, "Khay", "Thủy hải sản")
        ]
        for p in sample_products:
            c.execute("""
            INSERT INTO products (product_id, name, barcode, price, unit, category)
            VALUES (?, ?, ?, ?, ?, ?)
            """, p)
        conn.commit()


def get_products():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products ORDER BY product_id")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def park_order(store_id, terminal_id, cashier_id, customer_id, total_amount, order_items):
    today_str = datetime.now().strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:4].upper()
    park_id = f"HOLD-{today_str}-{short_uuid}"
    expires_at = (datetime.utcnow() + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO parked_orders 
    (park_id, store_id, terminal_id, cashier_id, customer_id, total_amount, order_items_json, status, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'SUSPENDED', ?)
    """, (park_id, store_id, terminal_id, cashier_id, customer_id, total_amount, json.dumps(order_items), expires_at))
    conn.commit()
    conn.close()
    return park_id, expires_at


def resume_order(park_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM parked_orders WHERE park_id = ? AND status = 'SUSPENDED'", (park_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None

    c.execute("UPDATE parked_orders SET status = 'RESUMED' WHERE park_id = ?", (park_id,))
    conn.commit()
    order = dict(row)
    order["items"] = json.loads(order["order_items_json"])
    conn.close()
    return order


def get_all_parked_orders():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM parked_orders WHERE status = 'SUSPENDED' ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


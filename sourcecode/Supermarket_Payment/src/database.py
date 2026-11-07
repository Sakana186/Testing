"""
database.py - Database Layer for Supermarket Offline Payment System
Uses SQLite3 (standard library) to store tokens, orders, parked carts, and anti-replay cache.
"""

import sqlite3
import json
import time
import uuid
from datetime import datetime, timedelta

DB_PATH = "supermarket_offline.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS nonce_replay_cache")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS parked_orders")
    cursor.execute("DROP TABLE IF EXISTS offline_payment_tokens")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS customers")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Customers / Members
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        wallet_balance REAL DEFAULT 2000000.0,
        loyalty_tier TEXT DEFAULT 'GOLD_VIP',
        credit_score INTEGER DEFAULT 750,
        pay_later_limit REAL DEFAULT 500000.0,
        pay_later_used REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Offline Payment Tokens (Pre-fetched by mobile device)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offline_payment_tokens (
        token_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        secret_key TEXT NOT NULL,
        max_single_limit REAL DEFAULT 1000000.0,
        max_accumulated_limit REAL DEFAULT 3000000.0,
        used_amount REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES customers(user_id)
    )
    """)

    # 3. Parked Orders (Suspended carts when user encounters issue)
    cursor.execute("""
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

    # 4. Offline / Online Transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        tx_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. Nonce / Anti-Replay Cache (In SQLite for zero-dependency persistence)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nonce_replay_cache (
        cache_key TEXT PRIMARY KEY,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )
    """)

    # 6. Sample Products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        barcode TEXT UNIQUE NOT NULL,
        price REAL NOT NULL,
        unit TEXT NOT NULL,
        category TEXT NOT NULL
    )
    """)

    conn.commit()
    seed_initial_data(conn)
    conn.close()


def seed_initial_data(conn):
    cursor = conn.cursor()

    # Seed Default Customer
    cursor.execute("SELECT COUNT(*) FROM customers WHERE user_id = 'USER_001'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO customers (user_id, name, phone, wallet_balance, loyalty_tier, credit_score, pay_later_limit, pay_later_used)
        VALUES ('USER_001', 'Nguyễn Văn An', '0912345678', 2500000.0, 'GOLD_VIP', 780, 500000.0, 0.0)
        """)

    # Seed Sample Products
    products = [
        ("P001", "Sữa tươi tiệt trùng Vinamilk 1L", "89346731001", 38000, "Hộp", "Sữa & Chế phẩm"),
        ("P002", "Thịt thăn bò Úc tươi 500g", "89346731002", 185000, "Khay", "Thịt tươi sống"),
        ("P003", "Bánh mì hoa cúc Harrys Pháp", "89346731003", 125000, "Gói", "Bánh mì"),
        ("P004", "Nước ép cam Vfresh 1L", "89346731004", 45000, "Hộp", "Đồ uống"),
        ("P005", "Gạo lứt đỏ ST25 hữu cơ 2kg", "89346731005", 95000, "Túi", "Lương thực"),
        ("P006", "Dầu oliu nguyên chất Olivo 500ml", "89346731006", 160000, "Chai", "Gia vị"),
        ("P007", "Rau chân vịt Đà Lạt 300g", "89346731007", 25000, "Gói", "Rau củ"),
        ("P008", "Cá hồi phi lê Na Uy tươi 300g", "89346731008", 220000, "Khay", "Thủy hải sản")
    ]

    for p in products:
        cursor.execute("""
        INSERT OR IGNORE INTO products (product_id, name, barcode, price, unit, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """, p)

    conn.commit()


def get_customer(user_id="USER_001"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_customer_balance(user_id, new_balance):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET wallet_balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()


def update_customer_pay_later(user_id, additional_used):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET pay_later_used = pay_later_used + ? WHERE user_id = ?", (additional_used, user_id))
    conn.commit()
    conn.close()


def get_products():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products ORDER BY product_id")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def prefetch_tokens(user_id="USER_001", count=5):
    """
    Simulates Cloud Gateway issuing pre-fetched offline tokens to mobile client.
    Each token has a secret key, 24h lifetime, and limits.
    """
    import secrets
    conn = get_connection()
    c = conn.cursor()

    # Check existing valid tokens
    c.execute("""
    SELECT * FROM offline_payment_tokens 
    WHERE user_id = ? AND is_active = 1 AND expires_at > datetime('now')
    """, (user_id,))
    existing = [dict(r) for r in c.fetchall()]

    if len(existing) >= count:
        conn.close()
        return existing

    tokens_to_create = count - len(existing)
    created = []
    for _ in range(tokens_to_create):
        token_id = f"TOK_{uuid.uuid4().hex[:12].upper()}"
        secret_key = secrets.token_hex(32)
        expires_at = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
        INSERT INTO offline_payment_tokens 
        (token_id, user_id, secret_key, max_single_limit, max_accumulated_limit, used_amount, is_active, expires_at)
        VALUES (?, ?, ?, 1000000.0, 3000000.0, 0.0, 1, ?)
        """, (token_id, user_id, secret_key, expires_at))
        created.append({
            "token_id": token_id,
            "user_id": user_id,
            "secret_key": secret_key,
            "max_single_limit": 1000000.0,
            "max_accumulated_limit": 3000000.0,
            "used_amount": 0.0,
            "expires_at": expires_at
        })

    conn.commit()
    conn.close()
    return existing + created


def get_token(token_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM offline_payment_tokens WHERE token_id = ?", (token_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_token_used(token_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE offline_payment_tokens 
    SET used_amount = used_amount + ?, is_active = CASE WHEN used_amount + ? >= max_accumulated_limit THEN 0 ELSE 1 END
    WHERE token_id = ?
    """, (amount, amount, token_id))
    conn.commit()
    conn.close()


def park_order(store_id, terminal_id, cashier_id, customer_id, total_amount, order_items):
    """
    Suspends a shopping cart with status 'SUSPENDED', generating a park barcode ticket.
    """
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
    """
    Restores a suspended cart and marks it as RESUMED.
    """
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


def is_nonce_used(cache_key):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM nonce_replay_cache WHERE cache_key = ?", (cache_key,))
    row = c.fetchone()
    conn.close()
    return row is not None


def record_nonce(cache_key, ttl_seconds=180):
    expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO nonce_replay_cache (cache_key, expires_at) VALUES (?, ?)", (cache_key, expires_at))
    # Clean up old expired nonces
    c.execute("DELETE FROM nonce_replay_cache WHERE expires_at < datetime('now')")
    conn.commit()
    conn.close()


def record_transaction(order_id, user_id, amount, payment_method, status, details=""):
    tx_id = f"TX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO transactions (tx_id, order_id, user_id, amount, payment_method, status, details)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, order_id, user_id, amount, payment_method, status, details))
    conn.commit()
    conn.close()
    return tx_id


def get_recent_transactions(limit=15):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

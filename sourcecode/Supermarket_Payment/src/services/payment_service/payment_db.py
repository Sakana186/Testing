"""
payment_db.py - Database Layer for Payment & Fraud Microservice
Owns its own isolated database: payment.db (Database-per-Service pattern).
Manages transactions ledger and Anti-Replay Nonce cache.
"""

import sqlite3
import uuid
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payment.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS transactions")
    c.execute("DROP TABLE IF EXISTS nonce_replay_cache")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS nonce_replay_cache (
        cache_key TEXT PRIMARY KEY,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )
    """)

    conn.commit()
    conn.close()


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


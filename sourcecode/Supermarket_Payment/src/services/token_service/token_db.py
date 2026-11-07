"""
token_db.py - Database Layer for Token Vault Microservice
Owns its own isolated database: tokens.db (Database-per-Service pattern).
"""

import sqlite3
import uuid
import secrets
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokens.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS offline_payment_tokens")
    conn.commit()
    conn.close()
    init_db()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS offline_payment_tokens (
        token_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        secret_key TEXT NOT NULL,
        max_single_limit REAL DEFAULT 1000000.0,
        max_accumulated_limit REAL DEFAULT 3000000.0,
        used_amount REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def prefetch_tokens(user_id="USER_001", count=5):
    conn = get_connection()
    c = conn.cursor()

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


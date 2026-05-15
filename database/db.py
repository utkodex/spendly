import sqlite3
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash


DB_PATH = Path(__file__).resolve().parent.parent / "spendly.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        if row["n"] > 0:
            return

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid

        now = datetime.now()
        year, month = now.year, now.month

        def d(day):
            return f"{year:04d}-{month:02d}-{day:02d}"

        expenses = [
            (user_id, 12.50,  "Food",          d(2),  "Lunch at cafe"),
            (user_id, 45.00,  "Transport",     d(4),  "Monthly metro pass"),
            (user_id, 120.00, "Bills",         d(5),  "Electricity bill"),
            (user_id, 30.00,  "Health",        d(8),  "Pharmacy"),
            (user_id, 18.75,  "Entertainment", d(11), "Movie ticket"),
            (user_id, 65.40,  "Shopping",      d(14), "New shoes"),
            (user_id, 9.99,   "Other",         d(17), "Subscription"),
            (user_id, 22.30,  "Food",          d(21), "Groceries"),
        ]

        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            expenses,
        )
        conn.commit()
    finally:
        conn.close()

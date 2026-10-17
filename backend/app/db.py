import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "paper.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            topic TEXT,
            image_url TEXT,
            published TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            embedding BLOB
        )""")
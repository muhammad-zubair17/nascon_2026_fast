import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "paper.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
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
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            free_text TEXT,
            vector BLOB,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_topics (
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            PRIMARY KEY (user_id, topic)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS editions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, date)
        );
        """)
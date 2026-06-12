"""
SQLite database connection and table initialization.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import settings


def get_db_path() -> str:
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


def init_db():
    """Create tables if they don't exist."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ── students table ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id   TEXT PRIMARY KEY,
            name         TEXT,
            age          INTEGER,
            education    TEXT,
            is_weak_foundation INTEGER DEFAULT 0,
            learning_goals TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── messages table ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT NOT NULL,
            session_id   TEXT NOT NULL,
            role         TEXT NOT NULL,   -- 'student' or 'assistant'
            content      TEXT NOT NULL,
            agent_name   TEXT,            -- which agent produced this
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── qa_records table ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_records (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT NOT NULL,
            question     TEXT NOT NULL,
            answer       TEXT NOT NULL,
            source       TEXT NOT NULL,   -- 'knowledge_base' or 'tavily_search'
            similarity_score REAL,
            topic_tags   TEXT,
            is_guided    INTEGER DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── sessions table ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id   TEXT PRIMARY KEY,
            student_id   TEXT NOT NULL,
            created_at   TEXT,
            is_active    INTEGER DEFAULT 1,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
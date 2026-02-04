import sqlite3
from pathlib import Path

DB_PATH = Path("data/todo.db")

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                due_date DATE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                time_hhmm TEXT NOT NULL,
                next_fire_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_fired_at TEXT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_user_next_active
            ON reminders (user_id, next_fire_at, is_active)
        """)

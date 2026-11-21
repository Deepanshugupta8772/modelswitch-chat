"""SQLite schema initialization for the backend skeleton."""

import sqlite3
from pathlib import Path

from .config import get_settings


def _database_path(database_url: str) -> str:
    if database_url == "sqlite:///:memory:":
        return ":memory:"
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("DATABASE_URL must use SQLite")
    path = database_url[len(prefix) :]
    if not path:
        raise ValueError("DATABASE_URL must include a database path")
    return path


def initialize_database() -> None:
    """Create the database parent directory and required messages table."""
    database_path = _database_path(get_settings().database_url)
    if database_path != ":memory:":
        Path(database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
            """)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)"
        )

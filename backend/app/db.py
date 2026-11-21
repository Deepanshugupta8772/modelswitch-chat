"""SQLite schema initialization for the backend skeleton."""

import sqlite3
import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
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


def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    """Return a session's stored messages in insertion order."""
    database_path = _database_path(get_settings().database_url)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT role, content, metadata, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def save_exchange(
    session_id: str,
    user_message: str,
    assistant_message: str,
    metadata: dict[str, Any],
) -> None:
    """Store both sides of a successful exchange atomically."""
    database_path = _database_path(get_settings().database_url)
    created_at = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.executemany(
                """
                INSERT INTO messages (session_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    (session_id, "user", user_message, None, created_at),
                    (
                        session_id,
                        "assistant",
                        assistant_message,
                        json.dumps(metadata),
                        created_at,
                    ),
                ),
            )

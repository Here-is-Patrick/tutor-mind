"""
Long-term memory: persists conversation messages and QA records to SQLite.
"""

import logging
from datetime import datetime
from typing import Optional

from app.models.database import get_db

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Persistent storage for conversations and QA records."""

    def save_message(
        self,
        student_id: str,
        session_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
    ):
        """Persist a single message to SQLite."""
        with get_db() as db:
            db.execute(
                """INSERT INTO messages (student_id, session_id, role, content, agent_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, session_id, role, content, agent_name),
            )
            db.commit()

    def save_qa_record(
        self,
        student_id: str,
        question: str,
        answer: str,
        source: str,
        similarity_score: Optional[float] = None,
        topic_tags: Optional[str] = None,
        is_guided: bool = False,
    ) -> int:
        """Persist a QA record to SQLite. Returns the new record's ID."""
        with get_db() as db:
            cursor = db.execute(
                """INSERT INTO qa_records
                   (student_id, question, answer, source, similarity_score, topic_tags, is_guided)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (student_id, question, answer, source, similarity_score, topic_tags, int(is_guided)),
            )
            db.commit()
            return cursor.lastrowid

    def get_session_messages(self, session_id: str, limit: int = 50) -> list[dict]:
        """Retrieve messages for a session in chronological order (oldest first)."""
        with get_db() as db:
            rows = db.execute(
                """SELECT role, content, agent_name, created_at
                   FROM messages WHERE session_id = ?
                   ORDER BY created_at ASC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_student_qa_history(self, student_id: str, limit: int = 20) -> list[dict]:
        """Retrieve recent QA records for a student."""
        with get_db() as db:
            rows = db.execute(
                """SELECT question, answer, source, similarity_score, topic_tags, is_guided, created_at
                   FROM qa_records WHERE student_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (student_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_or_create_session(self, student_id: str) -> str:
        """Get active session or create a new one."""
        import uuid
        with get_db() as db:
            row = db.execute(
                "SELECT session_id FROM sessions WHERE student_id = ? AND is_active = 1",
                (student_id,),
            ).fetchone()
            if row:
                return row["session_id"]
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            db.execute(
                "INSERT INTO sessions (session_id, student_id, created_at) VALUES (?, ?, ?)",
                (session_id, student_id, now),
            )
            db.commit()
            return session_id

    def create_new_session(self, student_id: str) -> str:
        """Always create a brand new session."""
        import uuid
        with get_db() as db:
            # Deactivate existing sessions
            db.execute(
                "UPDATE sessions SET is_active = 0 WHERE student_id = ?",
                (student_id,),
            )
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            db.execute(
                "INSERT INTO sessions (session_id, student_id, is_active, created_at) VALUES (?, ?, 1, ?)",
                (session_id, student_id, now),
            )
            db.commit()
            return session_id
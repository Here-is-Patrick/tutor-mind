"""
Short-term memory: sliding window conversation buffer.
"""

from collections import defaultdict

from app.config import settings


class ShortTermMemory:
    """
    In-memory sliding window per session.
    Stores up to `max_short_term_messages` messages per session.
    """

    def __init__(self):
        self._buffers: dict[str, list[dict]] = defaultdict(list)
        self.max_messages = settings.max_short_term_messages

    def add(self, session_id: str, role: str, content: str):
        """Add a message to the session buffer."""
        self._buffers[session_id].append({"role": role, "content": content})
        # Enforce sliding window
        if len(self._buffers[session_id]) > self.max_messages:
            self._buffers[session_id] = self._buffers[session_id][-self.max_messages:]

    def get_history(self, session_id: str, limit: int | None = None) -> list[dict]:
        """Get recent conversation history for a session."""
        msgs = self._buffers.get(session_id, [])
        if limit:
            msgs = msgs[-limit:]
        return msgs

    def get_formatted(self, session_id: str, limit: int | None = None) -> str:
        """Get formatted conversation as a single string for LLM context."""
        history = self.get_history(session_id, limit)
        lines = []
        for msg in history:
            role_label = "学生" if msg["role"] == "student" else "老师"
            lines.append(f"{role_label}: {msg['content']}")
        return "\n".join(lines)

    def clear(self, session_id: str):
        """Clear session memory."""
        self._buffers.pop(session_id, None)
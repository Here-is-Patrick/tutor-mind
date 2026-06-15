"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Student ──────────────────────────────────────────────────

class StudentProfile(BaseModel):
    student_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None
    is_weak_foundation: bool = False
    learning_goals: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        return (self.age is not None
                and self.education is not None
                and self.name is not None)

    def missing_fields(self) -> list[str]:
        """Return list of missing required fields."""
        missing = []
        if self.name is None:
            missing.append("name")
        if self.age is None:
            missing.append("age")
        if self.education is None:
            missing.append("education")
        return missing


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None
    is_weak_foundation: Optional[bool] = None
    learning_goals: Optional[str] = None


# ── Chat ─────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    student_id: str
    session_id: str
    message: str


class ChatResponse(BaseModel):
    student_id: str
    session_id: str
    reply: str
    agent_name: str                # which agent handled the response
    stage: str                     # current pipeline stage
    is_guided: bool = False        # whether socratic guidance was used
    metadata: Optional[dict] = None


# ── Session ──────────────────────────────────────────────────

class SessionCreate(BaseModel):
    student_id: str


class SessionResponse(BaseModel):
    session_id: str
    student_id: str
    created_at: datetime
    is_active: bool


# ── QA Record ────────────────────────────────────────────────

class QARecord(BaseModel):
    id: int
    student_id: str
    question: str
    answer: str
    source: str
    similarity_score: Optional[float] = None
    topic_tags: Optional[str] = None
    is_guided: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SimilarQuestion(BaseModel):
    question: str
    answer: str
    similarity_score: float
    qa_record_id: int


# ── Learning Analytics ───────────────────────────────────────

class LearningReport(BaseModel):
    student_id: str
    total_questions: int
    guided_sessions: int
    search_sessions: int
    common_topics: list[str]
    weak_foundation: bool
    created_at: datetime


# ── Error ────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
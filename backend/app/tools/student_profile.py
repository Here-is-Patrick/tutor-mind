"""
Student profile CRUD tools.
"""

import logging
from datetime import datetime
from typing import Optional

from app.models.database import get_db
from app.models.schemas import StudentProfile

logger = logging.getLogger(__name__)


def get_student_profile(student_id: str) -> Optional[StudentProfile]:
    """Retrieve a student's profile from SQLite, or None."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    if not row:
        return None
    return StudentProfile(
        student_id=row["student_id"],
        name=row["name"],
        age=row["age"],
        education=row["education"],
        is_weak_foundation=bool(row["is_weak_foundation"]),
        learning_goals=row["learning_goals"],
    )


def save_student_profile(profile: StudentProfile):
    """Insert or replace a student profile."""
    with get_db() as db:
        db.execute(
            """INSERT OR REPLACE INTO students
               (student_id, name, age, education, is_weak_foundation, learning_goals, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                profile.student_id,
                profile.name,
                profile.age,
                profile.education,
                int(profile.is_weak_foundation),
                profile.learning_goals,
                datetime.now().isoformat(),
            ),
        )
        db.commit()
    logger.info(f"Saved student profile: {profile.student_id}")


def update_student_profile(student_id: str, **kwargs):
    """Update specific fields on a student profile."""
    profile = get_student_profile(student_id)
    if profile is None:
        profile = StudentProfile(student_id=student_id)
    for key, value in kwargs.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    save_student_profile(profile)
    return profile


def has_complete_info(student_id: str) -> bool:
    """Check if student has all required info (age, education, name)."""
    profile = get_student_profile(student_id)
    if profile is None:
        return False
    return profile.is_complete()


def get_missing_info_message(student_id: str) -> Optional[str]:
    """
    Generate a polite message asking for missing student information.
    Returns None if profile is complete.
    """
    profile = get_student_profile(student_id)
    if profile is None:
        return (
            "你好！我是你的学习辅导助手 TutorMind。在开始之前，我想先了解一下你的情况。"
            "请问你的名字是什么？你多大了？目前在读什么阶段（如初中、高中、大学等）？"
            "你觉得自己的基础怎么样呢？"
        )

    missing = profile.missing_fields()
    if not missing:
        return None

    field_labels = {
        "name": "你的名字",
        "age": "你的年龄",
        "education": "你目前的学历/年级",
    }
    fields_str = "、".join(field_labels[f] for f in missing)
    if "education" in missing:
        return (
            f"我还需要了解一下{fields_str}，以及你觉得自己的基础怎么样呢？"
            "是基础比较薄弱，还是有一定基础？这样我可以更好地调整教学方式。"
        )
    return f"我还需要了解一下{fields_str}，方便我更好地为你提供帮助。可以告诉我吗？"
"""
Student API endpoints.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import StudentProfile, StudentProfileUpdate, ErrorResponse
from app.tools.student_profile import get_student_profile, save_student_profile, update_student_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/{student_id}", response_model=StudentProfile)
async def get_student(student_id: str):
    """Get student profile by ID."""
    profile = get_student_profile(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return profile


@router.put("/{student_id}", response_model=StudentProfile)
async def update_student(student_id: str, update: StudentProfileUpdate):
    """Update student profile fields."""
    updates = update.dict(exclude_unset=True)
    profile = update_student_profile(student_id, **updates)
    return profile


@router.post("/", response_model=StudentProfile)
async def create_student(profile: StudentProfile):
    """Create a new student profile."""
    save_student_profile(profile)
    return profile


@router.get("/{student_id}/history")
async def get_student_history(student_id: str, limit: int = 20):
    """Get QA history for a student."""
    from app.memory.long_term import LongTermMemory
    lt = LongTermMemory()
    history = lt.get_student_qa_history(student_id, limit)
    return {"student_id": student_id, "history": history}
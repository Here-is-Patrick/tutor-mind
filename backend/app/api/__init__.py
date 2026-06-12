"""
FastAPI API routes.
"""
from app.api.chat import router as chat_router
from app.api.student import router as student_router
from app.api.analytics import router as analytics_router

__all__ = ["chat_router", "student_router", "analytics_router"]
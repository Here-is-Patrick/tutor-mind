"""
Learning analytics API endpoints.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.database import get_db
from app.models.schemas import LearningReport
from app.tools.student_profile import get_student_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/{student_id}", response_model=LearningReport)
async def get_learning_report(student_id: str):
    """
    Generate a learning report for a student.
    Includes question counts, guided sessions, common topics, etc.
    """
    profile = get_student_profile(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student not found")

    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) FROM qa_records WHERE student_id = ?",
            (student_id,),
        ).fetchone()[0]

        guided = db.execute(
            "SELECT COUNT(*) FROM qa_records WHERE student_id = ? AND is_guided = 1",
            (student_id,),
        ).fetchone()[0]

        search = db.execute(
            "SELECT COUNT(*) FROM qa_records WHERE student_id = ? AND source = 'tavily_search'",
            (student_id,),
        ).fetchone()[0]

        # Get common topics (simple keyword extraction from questions)
        topics = db.execute(
            "SELECT question FROM qa_records WHERE student_id = ?",
            (student_id,),
        ).fetchall()

    # Simple topic extraction based on common keywords
    topic_keywords = {
        "数学": ["方程", "函数", "几何", "代数", "三角", "导数", "积分", "概率"],
        "物理": ["力", "速度", "加速度", "牛顿", "电", "磁", "光", "热"],
        "英语": ["语法", "单词", "阅读", "写作", "翻译", "听力"],
        "化学": ["元素", "反应", "化合", "分子", "原子"],
        "编程": ["Python", "代码", "算法", "函数", "变量"],
    }

    topic_counts = {}
    for row in topics:
        q = row["question"]
        for topic, keywords in topic_keywords.items():
            for kw in keywords:
                if kw in q:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    break

    common_topics = sorted(topic_counts, key=topic_counts.get, reverse=True)[:5]

    from datetime import datetime
    return LearningReport(
        student_id=student_id,
        total_questions=total,
        guided_sessions=guided,
        search_sessions=search,
        common_topics=common_topics,
        weak_foundation=profile.is_weak_foundation,
        created_at=datetime.now(),
    )


@router.get("/{student_id}/summary")
async def get_learning_summary(student_id: str):
    """Get a simple learning summary for a student."""
    with get_db() as db:
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        total = db.execute(
            "SELECT COUNT(*) FROM messages WHERE student_id = ?",
            (student_id,),
        ).fetchone()[0]

        recent = db.execute(
            "SELECT COUNT(*) FROM messages WHERE student_id = ? AND created_at > ?",
            (student_id, week_ago),
        ).fetchone()[0]

        sessions = db.execute(
            "SELECT COUNT(*) FROM sessions WHERE student_id = ?",
            (student_id,),
        ).fetchone()[0]

    return {
        "student_id": student_id,
        "total_messages": total,
        "recent_messages": recent,
        "total_sessions": sessions,
    }
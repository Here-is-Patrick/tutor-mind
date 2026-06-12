"""
Foundation check tool — provides adaptive instruction hints based on student ability level.
"""

from typing import Optional

from app.tools.student_profile import get_student_profile


ADAPTIVE_INSTRUCTIONS = {
    "weak": (
        "该学生基础薄弱，请遵循以下教学原则：\n"
        "1. 使用通俗易懂的语言，避免专业术语，必要时用日常生活中常见的例子做类比\n"
        "2. 将复杂概念拆解成小步骤，每次只讲一个点\n"
        "3. 苏格拉底引导的提问步长更小，每次只问最简单的下一步\n"
        "4. 多使用鼓励性语言，建立学生信心\n"
        "5. 如果学生表现出困惑，立刻回到更基础的层面解释"
    ),
    "normal": (
        "该学生有一定基础，可以适当使用专业术语，但仍需确保学生能跟上。\n"
        "提问步长可适中，根据学生回答灵活调整难度。"
    ),
}

DEFAULT_ADAPTIVE_TEXT = (
    "请以清晰、耐心的方式回答学生问题。"
    "如果学生表现出困惑，尝试用不同的方式解释。"
)


def get_adaptive_instructions(student_id: str) -> str:
    """
    Return adaptive instruction text for the given student.

    The instruction text tells the LLM how to tailor its response style
    based on whether the student has a weak foundation.
    """
    profile = get_student_profile(student_id)
    if profile is None:
        return DEFAULT_ADAPTIVE_TEXT
    if profile.is_weak_foundation:
        return ADAPTIVE_INSTRUCTIONS["weak"]
    return ADAPTIVE_INSTRUCTIONS["normal"]


def is_weak_foundation(student_id: str) -> Optional[bool]:
    """Return whether the student has a weak foundation, or None if unknown."""
    profile = get_student_profile(student_id)
    if profile is None:
        return None
    return profile.is_weak_foundation
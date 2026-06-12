"""Tool functions for TutorMind Agents."""
from app.tools.student_profile import (
    get_student_profile,
    save_student_profile,
    update_student_profile,
    has_complete_info,
    get_missing_info_message,
)
from app.tools.kb_search import search_knowledge_base
from app.tools.tavily_tool import tavily_search
from app.tools.foundation_check import get_adaptive_instructions
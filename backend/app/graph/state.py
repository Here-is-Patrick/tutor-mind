"""
LangGraph state definition for TutorMind pipeline.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class TutorState(TypedDict):
    """
    Centralized state object that flows through the LangGraph pipeline.

    Fields:
        student_id:       Unique student identifier
        session_id:       Current session identifier
        student_input:    Raw text input from the student
        student_profile:  Cached student profile (StudentProfile | None)
        is_info_complete: Whether student info is fully collected
        just_completed:   True if info was just completed in this turn (not a question)
        stage:            Current pipeline stage name
        kb_search_result: Knowledge base search result dict
        kb_hit:           Whether a similar QA was found in KB
        socratic_context: Context for Socratic teaching (similar Q&A)
        search_result:    Tavily search results
        final_reply:      Final assistant reply to the student
        is_weak_foundation: Whether student has weak foundation
        messages:         Annotated list of conversation messages
        error:            Error message if any
        mode:             Interaction mode (chat, quiz_question, quiz_answer, etc.)
        quiz_topic:       Topic for quiz generation
        quiz_difficulty:  Difficulty level for quiz
        quiz_question:    Current quiz question text
        quiz_reference:   Reference answer for the quiz
        quiz_student_answer: Student's answer to the quiz
        quiz_judge_result: Result of judging the quiz answer
    """

    student_id: str
    session_id: str
    student_input: str
    student_profile: Optional[dict]
    is_info_complete: bool
    just_completed: bool
    stage: str
    kb_search_result: Optional[dict]
    kb_hit: bool
    socratic_context: Optional[dict]
    search_result: Optional[list[dict]]
    final_reply: str
    is_weak_foundation: bool
    messages: Annotated[list, add_messages]
    error: Optional[str]
    mode: str
    quiz_topic: str
    quiz_difficulty: str
    quiz_question: str
    quiz_reference: str
    quiz_student_answer: str
    quiz_judge_result: Optional[dict]
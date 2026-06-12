"""
Tests for the LangGraph workflow pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.graph.state import TutorState
from app.graph.workflow import (
    check_student_info,
    route_after_check,
    route_after_collect,
    route_after_kb_search,
)


# ── State routing tests ───────────────────────────────────────

class TestRouting:
    def test_route_after_check_info_complete(self):
        state: TutorState = {
            "student_id": "s1",
            "session_id": "sess1",
            "student_input": "hello",
            "student_profile": None,
            "is_info_complete": True,
            "stage": "check_student_info",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert route_after_check(state) == "search_knowledge_base"

    def test_route_after_check_info_incomplete(self):
        state: TutorState = {
            "student_id": "s1",
            "session_id": "sess1",
            "student_input": "hello",
            "student_profile": None,
            "is_info_complete": False,
            "stage": "check_student_info",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert route_after_check(state) == "collect_info"

    def test_route_after_collect_still_incomplete(self):
        state: TutorState = {
            "student_id": "s1",
            "session_id": "sess1",
            "student_input": "hello",
            "student_profile": None,
            "is_info_complete": False,
            "stage": "collect_info",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert route_after_collect(state) == "__end__"

    def test_route_after_collect_now_complete(self):
        state: TutorState = {
            "student_id": "s1",
            "session_id": "sess1",
            "student_input": "hello",
            "student_profile": None,
            "is_info_complete": True,
            "stage": "collect_info",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert route_after_collect(state) == "search_knowledge_base"

    def test_route_after_kb_search_hit(self):
        state: TutorState = {
            "student_id": "s1",
            "session_id": "sess1",
            "student_input": "hello",
            "student_profile": None,
            "is_info_complete": True,
            "stage": "search_knowledge_base",
            "kb_search_result": {"found": True},
            "kb_hit": True,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert route_after_kb_search(state) == "socratic_teach"

    def test_route_after_kb_search_miss(self):
        state: TutorState = {
            "student_id": "s1",
            "session_id": "sess1",
            "student_input": "hello",
            "student_profile": None,
            "is_info_complete": True,
            "stage": "search_knowledge_base",
            "kb_search_result": {"found": False},
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert route_after_kb_search(state) == "tavily_search"


# ── Workflow structure tests ─────────────────────────────────

class TestWorkflowStructure:
    def test_build_workflow_returns_valid_graph(self):
        from app.graph.workflow import build_workflow
        workflow = build_workflow()
        assert workflow is not None

    def test_create_tutor_graph_compiles(self):
        from app.graph.workflow import create_tutor_graph
        graph = create_tutor_graph()
        assert graph is not None
        assert hasattr(graph, 'invoke')


# ── State initialization test ────────────────────────────────

class TestStateInit:
    def test_tutor_state_creation(self):
        state: TutorState = {
            "student_id": "test_student",
            "session_id": "test_session",
            "student_input": "什么是牛顿第二定律？",
            "student_profile": None,
            "is_info_complete": False,
            "stage": "start",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }
        assert state["student_id"] == "test_student"
        assert state["student_input"] == "什么是牛顿第二定律？"
"""
Tests for Agent basic functionality.
"""

import pytest

from app.agents.info_collector import InfoCollectorAgent
from app.agents.knowledge_retriever import KnowledgeRetrieverAgent


class TestInfoCollector:
    def test_check_nonexistent(self):
        from app.models.database import init_db
        init_db()
        agent = InfoCollectorAgent()
        result = agent.check("non_existent")
        assert result["is_complete"] is False
        assert result["profile"] is None

    def test_extract_regex_fallback(self):
        agent = InfoCollectorAgent()
        from app.models.schemas import StudentProfile
        profile = StudentProfile(student_id="test")
        result = agent._extract_regex("我今年15岁，基础比较薄弱", profile)
        assert result["age"] == 15
        assert result["is_weak_foundation"] is True


class TestKnowledgeRetriever:
    def test_search_returns_found_boolean(self):
        # Mock isn't needed just to check the interface
        agent = KnowledgeRetrieverAgent()
        # Should return a dict with found key
        result = agent.search("test question")
        assert "found" in result
        assert "similar_questions" in result
        assert isinstance(result["found"], bool)
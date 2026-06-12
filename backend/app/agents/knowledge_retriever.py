"""
KnowledgeRetrieverAgent — queries ChromaDB for similar historical Q&A.
"""

import logging
from typing import Optional

from app.config import settings
from app.tools.kb_search import search_knowledge_base

logger = logging.getLogger(__name__)


class KnowledgeRetrieverAgent:
    """
    Agent responsible for:
    1. Searching the knowledge base for similar questions
    2. Determining if a match is good enough for Socratic teaching
    """

    def search(self, question: str) -> dict:
        """
        Search knowledge base for similar Q&A.

        Returns:
            {
                "found": bool,
                "similar_questions": list[dict],
                "best_match": dict or None
            }
        """
        logger.info(f"KB search: {question[:60]}...")
        result = search_knowledge_base(question, top_k=settings.top_k_retrieval)
        logger.info(
            f"KB search result: found={result['found']}, "
            f"matches={len(result['similar_questions'])}"
        )
        return result

    def get_cached_answer(self, question: str) -> Optional[str]:
        """Try to get a cached answer from KB. Used for exact-match lookup."""
        result = self.search(question)
        if result["found"] and result["similar_questions"]:
            best = result["similar_questions"][0]
            if best["similarity_score"] >= 0.90:
                return best["answer"]
        return None
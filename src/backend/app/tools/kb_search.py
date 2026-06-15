"""
Knowledge base search tool — ChromaDB vector retrieval.
"""

import logging
from typing import Optional

from app.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)

# Singleton retriever instance
_retriever: Optional[KnowledgeRetriever] = None


def _get_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


def search_knowledge_base(question: str, top_k: int | None = None, student_id: str | None = None) -> dict:
    """
    Search the knowledge base for similar historical Q&A.

    Args:
        student_id: If provided, only return results from this student.

    Returns:
        {
            "found": bool,
            "similar_questions": list[dict],
            "best_match": dict or None
        }
    """
    retriever = _get_retriever()
    return retriever.retrieve(question, top_k, student_id=student_id)


def save_to_knowledge_base(
    qa_id: str,
    question: str,
    answer: str,
    metadata: dict | None = None,
):
    """Save a QA pair to the vector store."""
    retriever = _get_retriever()
    retriever.save_qa(qa_id, question, answer, metadata)
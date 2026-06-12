"""
Knowledge Retriever - coordinates embedding generation and vector search.
"""

import logging
from typing import Optional

from app.config import settings
from app.rag.embeddings import DashScopeEmbeddings
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """
    Encapsulates the full retrieval pipeline:
    1. Embed the query
    2. Search ChromaDB for similar QAs
    3. Filter by similarity threshold
    """

    def __init__(self):
        self.embeddings = DashScopeEmbeddings()
        self.vector_store = VectorStore()
        self.threshold = settings.similarity_threshold

    def retrieve(self, question: str, top_k: int | None = None, student_id: str | None = None) -> dict:
        """
        Retrieve similar QAs for a question.

        Args:
            student_id: If provided, only return results belonging to this student.

        Returns:
            {
                "found": bool,
                "similar_questions": list[dict],
                "best_match": dict or None
            }
        """
        try:
            query_embedding = self.embeddings.embed_query(question)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return {"found": False, "similar_questions": [], "best_match": None}

        all_matches = self.vector_store.search_similar(query_embedding, top_k)

        # Filter by threshold
        qualified = [m for m in all_matches if m["similarity_score"] >= self.threshold]

        # Filter by student_id if provided (check metadata)
        if student_id is not None:
            qualified = [
                m for m in qualified
                if m.get("metadata", {}).get("student_id") == student_id
            ]

        qualified.sort(key=lambda x: x["similarity_score"], reverse=True)

        best = qualified[0] if qualified else None
        return {
            "found": len(qualified) > 0,
            "similar_questions": qualified,
            "best_match": best,
        }

    def save_qa(self, qa_id: str, question: str, answer: str, metadata: Optional[dict] = None):
        """Save a new QA record to the vector store."""
        embedding = self.embeddings.embed_query(question)
        self.vector_store.add_qa(qa_id, question, answer, embedding, metadata)
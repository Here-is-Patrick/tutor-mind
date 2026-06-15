"""
ChromaDB vector store for historical Q&A embeddings.
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages ChromaDB collection for QA embeddings."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_qa(
        self,
        qa_id: str,
        question: str,
        answer: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
    ):
        """Insert a QA pair into the vector store."""
        doc_text = f"Q: {question}\nA: {answer}"
        meta = metadata or {}
        meta["question"] = question
        meta["answer"] = answer

        self.collection.add(
            ids=[qa_id],
            embeddings=[embedding],
            documents=[doc_text],
            metadatas=[meta],
        )
        logger.debug(f"Added QA record {qa_id} to ChromaDB")

    def search_similar(
        self, query_embedding: list[float], top_k: int | None = None
    ) -> list[dict]:
        """
        Search for similar QA records by embedding.

        Returns list of dicts: {id, question, answer, similarity_score, metadata}
        """
        k = top_k or settings.top_k_retrieval
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        similar = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 1.0
                # ChromaDB uses cosine distance; convert to similarity
                similarity = 1.0 - distance
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                similar.append({
                    "id": doc_id,
                    "question": meta.get("question", ""),
                    "answer": meta.get("answer", ""),
                    "similarity_score": round(similarity, 4),
                    "metadata": meta,
                })
        return similar

    def count(self) -> int:
        """Return number of records in collection."""
        return self.collection.count()
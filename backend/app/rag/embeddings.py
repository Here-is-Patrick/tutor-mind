"""
Embedding provider using Aliyun Bailian (DashScope) text-embedding models.
"""

from typing import List

from app.config import settings


class DashScopeEmbeddings:
    """Wrapper around DashScope text-embedding API."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.embedding_model

    def embed_query(self, text: str) -> list[float]:
        """Embed a single text string. Returns a list of floats."""
        import dashscope
        from dashscope import TextEmbedding

        resp = TextEmbedding.call(
            model=self.model,
            input=text,
            api_key=settings.dashscope_api_key,
        )
        if resp.status_code == 200:
            return resp.output["embeddings"][0]["embedding"]
        else:
            raise RuntimeError(
                f"DashScope embedding failed: {resp.code} - {resp.message}"
            )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings (batch)."""
        return [self.embed_query(t) for t in texts]
"""
Configuration management for TutorMind.
All sensitive values are loaded from environment variables — no hardcoded keys.
"""

import os
from pathlib import Path
from typing import Optional, List

# Load .env file if present
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, str(default).lower())
    return val.lower() in ("true", "1", "yes", "on")


def _env_int(key: str, default: int = 0) -> int:
    return int(os.environ.get(key, str(default)))


def _env_float(key: str, default: float = 0.0) -> float:
    return float(os.environ.get(key, str(default)))


def _env_list(key: str, default: List[str] = None) -> List[str]:
    if default is None:
        default = []
    val = os.environ.get(key, "")
    if not val:
        return default
    # Try JSON list format first, then comma-separated
    import json
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return [v.strip() for v in val.split(",") if v.strip()]


class Settings:
    """Configuration loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    app_name: str = _env_str("APP_NAME", "TutorMind")
    app_version: str = _env_str("APP_VERSION", "0.1.0")
    debug: bool = _env_bool("DEBUG", False)
    host: str = _env_str("HOST", "0.0.0.0")
    port: int = _env_int("PORT", 8000)

    # ── Aliyun Bailian (DashScope) ───────────────────────────────
    dashscope_api_key: str = _env_str("DASHSCOPE_API_KEY", "")
    llm_model: str = _env_str("LLM_MODEL", "qwen-plus")
    embedding_model: str = _env_str("EMBEDDING_MODEL", "text-embedding-v2")

    # ── Tavily Search ────────────────────────────────────────────
    tavily_api_key: str = _env_str("TAVILY_API_KEY", "")

    # ── ChromaDB ────────────────────────────────────────────────
    chroma_persist_dir: str = _env_str("CHROMA_PERSIST_DIR", "./data/chroma_db")
    chroma_collection_name: str = _env_str("CHROMA_COLLECTION_NAME", "qa_embeddings")

    # ── SQLite ───────────────────────────────────────────────────
    sqlite_path: str = _env_str("SQLITE_PATH", "./data/tutor_mind.db")

    # ── Knowledge Retrieval ──────────────────────────────────────
    similarity_threshold: float = _env_float("SIMILARITY_THRESHOLD", 0.75)
    top_k_retrieval: int = _env_int("TOP_K_RETRIEVAL", 3)

    # ── Conversation ─────────────────────────────────────────────
    max_short_term_messages: int = _env_int("MAX_SHORT_TERM_MESSAGES", 20)

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: List[str] = _env_list("CORS_ORIGINS", ["http://localhost:5173", "http://localhost:3000"])


settings = Settings()

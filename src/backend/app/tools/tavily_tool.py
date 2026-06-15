"""
Tavily Search API wrapper tool.
"""

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

TAVILY_API_URL = "https://api.tavily.com/search"


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search Tavily for real-time information.

    Returns list of dicts with keys: title, url, content, score
    """
    import requests

    if not settings.tavily_api_key:
        logger.warning("Tavily API key not set; returning empty results.")
        return []

    try:
        resp = requests.post(
            TAVILY_API_URL,
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        logger.info(f"Tavily search returned {len(results)} results for: {query[:60]}")
        return results
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []


def format_search_results(results: list[dict]) -> str:
    """Format Tavily results into a markdown-like string."""
    if not results:
        return "未找到相关搜索结果。"

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        content = r.get("content", "")
        url = r.get("url", "")
        lines.append(f"### {i}. {title}")
        lines.append(f"{content[:500]}")
        if url:
            lines.append(f"来源: {url}")
        lines.append("")
    return "\n".join(lines)
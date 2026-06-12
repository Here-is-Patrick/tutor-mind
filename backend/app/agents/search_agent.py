"""
SearchAgent — calls Tavily API and generates answers from search results.
"""

import logging

from app.agents.orchestrator import get_orchestrator
from app.memory.long_term import LongTermMemory
from app.tools.tavily_tool import tavily_search, format_search_results
from app.tools.foundation_check import get_adaptive_instructions
from app.tools.kb_search import save_to_knowledge_base

logger = logging.getLogger(__name__)


class SearchAgent:
    """
    Agent responsible for:
    1. Calling Tavily Search API for real-time information
    2. Generating structured answers from search results
    3. Adapting language style based on student's foundation level
    """

    ANSWER_SYSTEM_PROMPT = """
你是一个知识渊博的学习辅导老师。请根据以下搜索结果，清晰准确地回答学生的问题。

{adaptive_instructions}

搜索结果：
{search_results}

对话历史：
{history}

学生问题：{query}

请用以下结构回答：
1. 先给出简洁的核心答案
2. 如果需要，再补充详细解释
3. 如果搜索结果信息不足，诚实告知并建议学生查阅其他资料
"""

    def search(self, student_id: str, query: str) -> dict:
        """
        Call Tavily search API and return raw results.
        """
        logger.info(f"SearchAgent searching: {query[:60]}...")
        results = tavily_search(query)
        return {"raw_results": results, "query": query}

    def generate_answer(
        self,
        student_id: str,
        query: str,
        search_results: list[dict],
        session_id: str,
    ) -> dict:
        """
        Generate a structured answer from search results, adapting to
        foundation level.
        """
        orchestrator = get_orchestrator()
        long_term = LongTermMemory()

        formatted_results = format_search_results(search_results)
        history = orchestrator.get_conversation_context(session_id)
        adaptive_instructions = get_adaptive_instructions(student_id)

        prompt = self.ANSWER_SYSTEM_PROMPT.format(
            adaptive_instructions=adaptive_instructions,
            search_results=formatted_results,
            history=history,
            query=query,
        )

        reply = orchestrator.call_llm(prompt, query, history)

        # Save to long-term memory
        qa_id = str(long_term.save_qa_record(
            student_id=student_id,
            question=query,
            answer=reply,
            source="tavily_search",
            is_guided=False,
        ))

        # Save to vector store for future reuse
        try:
            metadata = {
                "student_id": student_id,
                "source": "tavily_search",
                "is_guided": "false",
            }
            save_to_knowledge_base(qa_id, query, reply, metadata)
        except Exception as e:
            logger.warning(f"Failed to save to KB: {e}")

        logger.info(f"Answer generated for {student_id}: {reply[:60]}...")
        return {"reply": reply.strip()}
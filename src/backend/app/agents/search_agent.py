"""
SearchAgent — calls Tavily API and generates answers from search results.
"""

import logging

from langchain_core.messages import HumanMessage

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

学生问题：{query}

请用以下结构回答：
1. 先给出简洁的核心答案
2. 如果需要，再补充详细解释
3. 如果搜索结果信息不足，诚实告知并建议学生查阅其他资料

重要格式要求：
- 所有数学公式必须使用 LaTeX 格式，用 $ 包裹行内公式，用 $$ 包裹独立公式块。例如：$E=mc^2$ 或 $$\\int_a^b f(x)dx$$
- 所有代码片段必须用 Markdown 代码块包裹，并标明语言类型。例如：
```python
def hello():
    print("Hello")
```
- 禁止使用纯文本的数学表达式（如 f'(x_0) = lim... 这种没有 LaTeX 格式的写法）
- 禁止使用 ASCII 艺术或特殊字符拼凑的公式
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
        messages: list = None,
    ) -> dict:
        """
        Generate a structured answer from search results, adapting to
        foundation level. Supports multi-turn conversation via messages.
        """
        orchestrator = get_orchestrator()
        long_term = LongTermMemory()

        formatted_results = format_search_results(search_results)
        adaptive_instructions = get_adaptive_instructions(student_id)

        prompt = self.ANSWER_SYSTEM_PROMPT.format(
            adaptive_instructions=adaptive_instructions,
            search_results=formatted_results,
            query=query,
        )

        # Use multi-turn API if conversation history exists
        if messages is None:
            messages = []

        if messages:
            messages_with_current = list(messages)
            messages_with_current.append(HumanMessage(content=query))
            reply = orchestrator.call_llm_with_messages(
                system_prompt=prompt,
                messages=messages_with_current,
                adaptive_instructions=adaptive_instructions,
            )
        else:
            # Fallback to legacy API
            history = orchestrator.get_conversation_context(session_id)
            reply = orchestrator.call_llm(prompt, query, history=history)

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

"""
Orchestrator Agent — system coordinator and LLM communication hub.
"""

import logging
from typing import Optional

import dashscope

from app.config import settings
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.tools.foundation_check import get_adaptive_instructions

logger = logging.getLogger(__name__)

# Session-level memory
short_term_memory = ShortTermMemory()
long_term_memory = LongTermMemory()


class OrchestratorAgent:
    """
    Master orchestrator:
    - Coordinates the full pipeline
    - Provides LLM calling capability
    - Manages conversation context
    """

    def __init__(self):
        self.model = settings.llm_model

    def call_llm(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[str] = None,
        adaptive_instructions: Optional[str] = None,
    ) -> str:
        """Call the DashScope LLM and return the response text."""
        messages = []

        # Global formatting instruction appended to every system prompt
        formatting_instruction = """
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

        # Build system prompt
        full_system = system_prompt
        if adaptive_instructions:
            full_system += f"\n\n{adaptive_instructions}"
        full_system += f"\n\n{formatting_instruction}"
        messages.append({"role": "system", "content": full_system})

        # Add history if available
        if history:
            messages.append({"role": "user", "content": f"对话历史:\n{history}"})

        messages.append({"role": "user", "content": user_message})

        try:
            # Set API key globally for dashscope
            dashscope.api_key = settings.dashscope_api_key

            resp = dashscope.Generation.call(
                model=self.model,
                messages=messages,
                result_format="message",
            )
            if resp.status_code == 200:
                return resp.output.choices[0].message.content
            else:
                logger.error(f"LLM call failed: {resp.code} - {resp.message}")
                return f"抱歉，我暂时无法回答这个问题。请稍后再试。（错误：{resp.code}）"
        except Exception as e:
            logger.error(f"LLM call exception: {e}")
            return "抱歉，系统遇到了一个技术问题，请稍后再试。"

    def save_conversation_turn(
        self,
        student_id: str,
        session_id: str,
        student_input: str,
        assistant_reply: str,
        agent_name: str = "orchestrator",
    ):
        """Save a conversation turn to both short-term and long-term memory."""
        short_term_memory.add(session_id, "student", student_input)
        short_term_memory.add(session_id, "assistant", assistant_reply)

        long_term_memory.save_message(student_id, session_id, "student", student_input)
        long_term_memory.save_message(
            student_id, session_id, "assistant", assistant_reply, agent_name=agent_name
        )

    def get_conversation_context(self, session_id: str, limit: int = 10) -> str:
        """Get recent conversation context for a session.
        Falls back to long-term DB if short-term memory is empty (e.g. after server restart)."""
        context = short_term_memory.get_formatted(session_id, limit)
        if context:
            return context
        # Fallback: load from DB so history survives server restarts
        db_history = long_term_memory.get_session_messages(session_id, limit=limit)
        lines = []
        for msg in db_history:
            role_label = "学生" if msg["role"] == "student" else "老师"
            lines.append(f"{role_label}: {msg['content']}")
        return "\n".join(lines)


# ── Shared singleton ──────────────────────────────────────────────────

_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
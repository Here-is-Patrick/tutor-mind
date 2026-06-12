"""
SocraticTutorAgent — guides the student through Socratic questioning method.
"""

import logging

from app.agents.orchestrator import get_orchestrator
from app.memory.long_term import LongTermMemory
from app.tools.foundation_check import get_adaptive_instructions
from app.tools.kb_search import save_to_knowledge_base

logger = logging.getLogger(__name__)


class SocraticTutorAgent:
    """
    Implements the Socratic method:
    - Instead of giving the answer directly, ask a sequence of guiding questions
    - Student answers each question, assistant evaluates and asks next one
    - Eventually the student arrives at the answer themselves
    - Adapts question size based on student's foundation level
    """

    SYSTEM_PROMPT = """
你是一位采用苏格拉底教学法的老师。现在：
已知相似问题：{similar_question}
历史参考解答：{reference_answer}
学生当前问题：{current_question}

请根据参考解答，设计一个递进式的引导提问，帮助学生自己推导出答案。
**请只问一个问题**，不要一次性给出多个问题。
**不要直接给出答案**，只提问。

{adaptive_instructions}

对话历史：
{history}

现在输出你的下一个引导问题：
"""

    def teach(
        self,
        student_id: str,
        student_input: str,
        context: dict,
        session_id: str,
    ) -> dict:
        """
        Generate a Socratic guiding question based on similar question context.
        """
        orchestrator = get_orchestrator()
        long_term = LongTermMemory()

        similar_q = context.get("question", student_input)
        reference_a = context.get("answer", "")
        history = orchestrator.get_conversation_context(session_id)
        adaptive_instructions = get_adaptive_instructions(student_id)

        prompt = self.SYSTEM_PROMPT.format(
            similar_question=similar_q,
            reference_answer=reference_a,
            current_question=student_input,
            history=history,
            adaptive_instructions=adaptive_instructions,
        )

        reply = orchestrator.call_llm(prompt, student_input, history)

        # Save this interaction to long-term memory
        qa_id = str(long_term.save_qa_record(
            student_id=student_id,
            question=student_input,
            answer=reply,
            source="knowledge_base",
            similarity_score=context.get("similarity_score"),
            is_guided=True,
        ))

        # Save to vector store for future reuse
        try:
            metadata = {
                "student_id": student_id,
                "similarity_score": context.get("similarity_score"),
                "source": "knowledge_base",
                "is_guided": "true",
            }
            save_to_knowledge_base(qa_id, student_input, reply, metadata)
        except Exception as e:
            logger.warning(f"Failed to save to KB: {e}")

        logger.info(f"Socratic question generated for {student_id}: {reply[:60]}...")
        return {"reply": reply.strip()}
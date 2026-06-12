"""
QuizAgent — generates quiz questions, judges answers, and guides students.

Flow:
1. After answering a question, offer to generate a quiz
2. Generate quiz question via Tavily search (not made up)
3. Judge student's answer
4. If correct → encourage, ask if harder question wanted
5. If wrong → Socratic guidance or direct answer on request
"""

import logging
import json
import re

from app.agents.orchestrator import get_orchestrator
from app.tools.tavily_tool import tavily_search
from app.tools.foundation_check import get_adaptive_instructions

logger = logging.getLogger(__name__)


class QuizAgent:
    """
    Agent responsible for:
    1. Generating quiz questions based on topic (via search)
    2. Judging student answers
    3. Providing Socratic guidance or direct answers
    """

    GENERATE_QUESTION_PROMPT = """
你是一位出题老师。请根据以下搜索结果，为学生出一道关于「{topic}」的{difficulty}难度题目。

要求：
1. 题目必须基于搜索结果中的真实知识，不可杜撰
2. 题目要有明确的答案
3. 只输出题目本身，不要输出答案
4. 题目适合{education}水平的学生
5. **题目必须严格围绕「{topic}」这个知识点，不能偏离主题出其他不相关的题目**

搜索结果：
{search_results}

请用以下JSON格式输出：
{{
  "question": "题目内容",
  "reference_answer": "标准答案（用于评判）",
  "hint": "给学生的一个提示"
}}

严格只返回JSON，不要其他文字。
"""

    JUDGE_ANSWER_PROMPT = """
你是一位阅卷老师。

题目：{question}
标准答案：{reference_answer}
学生答案：{student_answer}

请评判学生答案是否正确。允许意思相近、表述不同的情况视为正确。

请用以下JSON格式输出：
{{
  "is_correct": true/false,
  "evaluation": "评价说明（指出对错并简要解释）",
  "encouragement": "鼓励或引导的话"
}}

严格只返回JSON，不要其他文字。
"""

    SOCRATIC_GUIDE_PROMPT = """
你是一位采用苏格拉底教学法的老师。

题目：{question}
标准答案：{reference_answer}
学生当前答案：{student_answer}

学生的答案是错误的。请设计一个引导提问，帮助学生自己思考出正确答案。
**请只问一个问题**，不要直接给出答案。

{adaptive_instructions}

现在输出你的引导问题：
"""

    DIRECT_ANSWER_PROMPT = """
你是一位耐心的老师。

题目：{question}
标准答案：{reference_answer}
学生当前答案：{student_answer}

学生要求直接给出答案。请：
1. 直接给出正确答案
2. 简要解释为什么这个答案是正确的
3. 鼓励学生继续学习

请用以下JSON格式输出：
{{
  "answer": "直接答案",
  "explanation": "简要解释"
}}

严格只返回JSON，不要其他文字。
"""

    def generate_question(
        self,
        student_id: str,
        topic: str,
        difficulty: str = "适中",
        education: str = "高中",
    ) -> dict:
        """Generate a quiz question via Tavily search."""
        logger.info(f"[QuizAgent] Generating quiz for {student_id}: topic={topic}, difficulty={difficulty}")

        # Clean up topic: remove markdown, emojis, and generic prefixes
        clean_topic = self._clean_topic(topic)
        logger.info(f"[QuizAgent] Cleaned topic: '{clean_topic}'")

        # Search for real questions/knowledge about the topic
        search_query = f"{clean_topic} {difficulty}难度 练习题 题目"
        search_results = tavily_search(search_query, max_results=5)

        if not search_results:
            # Fallback: try broader search
            search_results = tavily_search(clean_topic, max_results=5)

        from app.tools.tavily_tool import format_search_results
        formatted_results = format_search_results(search_results)

        orchestrator = get_orchestrator()
        adaptive = get_adaptive_instructions(student_id)

        prompt = self.GENERATE_QUESTION_PROMPT.format(
            topic=clean_topic,
            difficulty=difficulty,
            education=education,
            search_results=formatted_results,
        )

        reply = orchestrator.call_llm(prompt, "请出题")

        # Parse JSON response
        try:
            cleaned = self._clean_json(reply)
            data = json.loads(cleaned)
            logger.info(f"[QuizAgent] Generated question for {student_id}: {data.get('question', '')[:60]}...")
            return {
                "question": data.get("question", "").strip(),
                "reference_answer": data.get("reference_answer", "").strip(),
                "hint": data.get("hint", "").strip(),
                "search_results": search_results,
            }
        except Exception as e:
            logger.warning(f"[QuizAgent] Failed to parse quiz JSON: {e}, raw={reply[:200]}")
            # Fallback: return a simple message
            return {
                "question": f"请尝试解答以下问题：{clean_topic}的相关知识你了解多少？",
                "reference_answer": "需要具体搜索",
                "hint": "回想一下刚才学到的内容",
                "search_results": search_results,
            }

    def _clean_topic(self, topic: str) -> str:
        """Clean topic string by removing markdown, emojis, and generic instructional text."""
        import re
        # Remove markdown bold/italic markers
        t = topic.replace("**", "").replace("*", "").replace("__", "").replace("_", "")
        # Remove LaTeX math markers
        t = t.replace("$", "")
        # Remove common emoji and instructional prefixes
        prefixes_to_remove = [
            "要我出一道题来检验一下你的理解吗",
            "你可以回复",
            "回复",
            "你可以",
            "需要我带你一起做",
            "或者你想先问问",
            "想挑战更难的题目吗",
            "想继续练习吗",
            "请直接回复你的答案",
            "我会帮你评判",
        ]
        for prefix in prefixes_to_remove:
            t = t.replace(prefix, "")
        # Remove emoji characters (common ranges)
        t = re.sub(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]", "", t)
        # Remove extra whitespace
        t = re.sub(r"\s+", " ", t).strip(" ，。！？\n")
        return t

    def judge_answer(
        self,
        student_id: str,
        question: str,
        reference_answer: str,
        student_answer: str,
    ) -> dict:
        """Judge whether the student's answer is correct."""
        logger.info(f"[QuizAgent] Judging answer for {student_id}")

        orchestrator = get_orchestrator()
        prompt = self.JUDGE_ANSWER_PROMPT.format(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
        )
        reply = orchestrator.call_llm(prompt, "请评判")

        try:
            cleaned = self._clean_json(reply)
            data = json.loads(cleaned)
            return {
                "is_correct": data.get("is_correct", False),
                "evaluation": data.get("evaluation", ""),
                "encouragement": data.get("encouragement", ""),
            }
        except Exception as e:
            logger.warning(f"[QuizAgent] Failed to parse judge JSON: {e}")
            return {
                "is_correct": False,
                "evaluation": "无法评判，请再试一次",
                "encouragement": "没关系，再想想！",
            }

    def socratic_guide(
        self,
        student_id: str,
        question: str,
        reference_answer: str,
        student_answer: str,
    ) -> dict:
        """Provide Socratic guidance for a wrong answer."""
        logger.info(f"[QuizAgent] Socratic guide for {student_id}")

        orchestrator = get_orchestrator()
        adaptive = get_adaptive_instructions(student_id)
        prompt = self.SOCRATIC_GUIDE_PROMPT.format(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            adaptive_instructions=adaptive,
        )
        reply = orchestrator.call_llm(prompt, "请引导")
        return {"reply": reply.strip()}

    def direct_answer(
        self,
        student_id: str,
        question: str,
        reference_answer: str,
        student_answer: str,
    ) -> dict:
        """Give direct answer when student asks for it."""
        logger.info(f"[QuizAgent] Direct answer for {student_id}")

        orchestrator = get_orchestrator()
        prompt = self.DIRECT_ANSWER_PROMPT.format(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
        )
        reply = orchestrator.call_llm(prompt, "请给出答案")

        try:
            cleaned = self._clean_json(reply)
            data = json.loads(cleaned)
            return {
                "reply": f"📖 **正确答案**：{data.get('answer', '')}\n\n💡 **解析**：{data.get('explanation', '')}",
            }
        except Exception as e:
            logger.warning(f"[QuizAgent] Failed to parse direct answer JSON: {e}")
            return {
                "reply": f"📖 **正确答案**：{reference_answer}\n\n请回顾相关知识点，继续加油！",
            }

    def _clean_json(self, text: str) -> str:
        """Extract JSON from LLM response that may contain markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # Remove first and last fence lines
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

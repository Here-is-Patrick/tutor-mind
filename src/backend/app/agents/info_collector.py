"""
InfoCollectorAgent — checks student info completeness, collects missing data.
"""

import logging
from typing import Optional
import re

from app.models.schemas import StudentProfile
from app.tools.student_profile import (
    get_student_profile,
    save_student_profile,
    get_missing_info_message,
    has_complete_info,
)

logger = logging.getLogger(__name__)


class InfoCollectorAgent:
    """
    Agent responsible for:
    1. Checking if student info is complete
    2. Prompting for missing info
    3. Extracting and saving info from student's reply
    """

    SYSTEM_PROMPT = """
你是一个礼貌友好的学习助手，负责收集学生的基本信息：
- 姓名
- 年龄
- 学历/年级
- 基础水平：判断学生是「基础薄弱」还是「有一定基础」

请从学生的回复中提取这些信息。
如果学生提到多个信息，全部提取。
用JSON格式返回提取结果：
{
  "name": "姓名（如果找到）",
  "age": 年龄（数字，如果找到）,
  "education": "学历/年级文字描述（如果找到）",
  "is_weak_foundation": true/false/null,
  "summary": "你总结提取到了哪些信息"
}

如果找不到某个字段，值设为null。
严格只返回JSON，不包含其他文字。
"""

    # Signals that the user wants to update their profile info
    _UPDATE_SIGNALS = [
        '基础薄弱', '基础不好', '基础差', '基础一般', '基础还行', '基础不错',
        '有一定基础', '没有基础', '零基础',
        '我叫', '我是', '今年', '岁', '年级', '学历',
        '改一下', '修改', '更新', '换', '改成',
    ]

    def check(self, student_id: str) -> dict:
        """
        Check profile status.
        Returns: {"is_complete": bool, "profile": dict or None, "is_weak_foundation": bool}
        """
        profile = get_student_profile(student_id)
        if profile is None:
            return {
                "is_complete": False,
                "profile": None,
                "is_weak_foundation": False,
            }
        return {
            "is_complete": profile.is_complete(),
            "profile": profile.dict(),
            "is_weak_foundation": profile.is_weak_foundation,
        }

    def looks_like_profile_update(self, student_input: str) -> bool:
        """Heuristic: does the input look like the user is updating their profile?"""
        return any(sig in student_input for sig in self._UPDATE_SIGNALS)

    def collect(
        self,
        student_id: str,
        student_input: str,
        existing_profile: Optional[dict],
    ) -> dict:
        """
        Collect info from student input.
        Returns: {"reply": str, "is_complete": bool, "profile": dict}
        """
        from app.agents.orchestrator import get_orchestrator

        orchestrator = get_orchestrator()

        # If no existing profile, create a new one
        if existing_profile:
            profile = StudentProfile(**existing_profile)
        else:
            profile = StudentProfile(student_id=student_id)

        # Parse student response to extract info
        extracted = self._extract_info(student_input, profile, orchestrator)

        # Update profile
        if extracted.get("name"):
            profile.name = extracted["name"]
        if extracted.get("age") is not None:
            profile.age = int(extracted["age"])
        if extracted.get("education"):
            profile.education = extracted["education"]
        if extracted.get("is_weak_foundation") is not None:
            profile.is_weak_foundation = extracted["is_weak_foundation"]

        save_student_profile(profile)
        logger.info(f"Updated profile for {student_id}: {profile.dict()}")

        if not profile.is_complete():
            prompt_msg = get_missing_info_message(student_id) or "还有一些信息需要确认一下。"
            return {
                "reply": prompt_msg,
                "is_complete": False,
                "profile": profile.dict(),
            }

        return {
            "reply": f"你好，{profile.name or '同学'}！很高兴认识你。我已经了解了你的情况，现在开始提问吧！",
            "is_complete": True,
            "profile": profile.dict(),
        }

    def _extract_info(
        self,
        input_text: str,
        current_profile: StudentProfile,
        orchestrator,
    ) -> dict:
        """Use LLM to extract fields from natural language input."""
        try:
            response_text = orchestrator.call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=f"学生当前输入：{input_text}\n\n请提取信息。",
            )
            # Clean up response
            cleaned = response_text.strip()
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            import json
            data = json.loads(cleaned)
            return data
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to regex")
            return self._extract_regex(input_text, current_profile)

    def _extract_regex(self, text: str, profile: StudentProfile) -> dict:
        """Fallback regex extraction — comprehensive pattern matching."""
        result = {}

        # Extract name (e.g. "我叫张三", "我是李四", "张三，20岁")
        name_patterns = [
            r'我叫(\S{1,4})',
            r'我是(\S{1,4})',
            r'[，,]\s*(\S{1,4})\s*[，,]\d+',
            r'^\s*(\S{1,4})\s*[，,]',
        ]
        for pat in name_patterns:
            m = re.search(pat, text)
            if m:
                name = m.group(1).strip()
                # Filter out common non-name words
                if name not in ('我', '你', '他', '她', '它', '是', '叫', '岁', '年', '大'):
                    result["name"] = name
                    break

        # Extract age
        age_match = re.search(r'(\d+)\s*(岁|年|岁了|周岁)', text)
        if age_match:
            result["age"] = int(age_match.group(1))

        # Extract education
        edu_keywords = [
            '小学', '初中', '高中', '高一', '高二', '高三',
            '大学', '大一', '大二', '大三', '大四',
            '研究生', '硕士', '博士',
            '中专', '大专', '职高',
        ]
        for kw in edu_keywords:
            if kw in text:
                result["education"] = kw
                break

        # Extract weak foundation
        weak_signals = ['基础薄弱', '不好', '比较差', '很差', '不行', '薄弱', '一般', '不太好']
        strong_signals = ['有基础', '不错', '还行', '可以', '有一定基础', '挺好的', '扎实']
        if any(s in text for s in weak_signals):
            result["is_weak_foundation"] = True
        elif any(s in text for s in strong_signals):
            result["is_weak_foundation"] = False

        return result
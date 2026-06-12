"""
LangGraph StateGraph workflow — the master orchestrator for TutorMind.

Pipeline:
  1. check_student_info  →  if incomplete → collect_info → END
  2. search_knowledge_base → if hit → socratic_teach → END
  3. search_knowledge_base → if miss → tavily_search → generate_answer → END
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import TutorState
from app.agents.info_collector import InfoCollectorAgent
from app.agents.knowledge_retriever import KnowledgeRetrieverAgent
from app.agents.socratic_tutor import SocraticTutorAgent
from app.agents.search_agent import SearchAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)

# ── Agent instances ──────────────────────────────────────────────────

info_collector = InfoCollectorAgent()
kb_retriever = KnowledgeRetrieverAgent()
socratic_tutor = SocraticTutorAgent()
search_agent = SearchAgent()
quiz_agent = QuizAgent()
orchestrator = OrchestratorAgent()


# ── Node functions ───────────────────────────────────────────────────

def check_student_info(state: TutorState) -> TutorState:
    """
    Node 1: Check if student info is complete.
    """
    logger.info(f"[{state['student_id']}] Stage: check_student_info")
    result = info_collector.check(state["student_id"])
    state["is_info_complete"] = result["is_complete"]
    state["student_profile"] = result["profile"]
    state["is_weak_foundation"] = result.get("is_weak_foundation", False)
    state["stage"] = "check_student_info"
    return state


def collect_info(state: TutorState) -> TutorState:
    """
    Node 2a: Collect missing student info.
    If info becomes complete in this turn, mark just_completed=True
    so we return a confirmation instead of treating input as a question.
    """
    logger.info(f"[{state['student_id']}] Stage: collect_info")
    was_complete_before = state.get("is_info_complete", False)
    result = info_collector.collect(
        state["student_id"],
        state["student_input"],
        state["student_profile"],
    )
    state["final_reply"] = result["reply"]
    state["is_info_complete"] = result.get("is_complete", False)
    state["student_profile"] = result.get("profile", state["student_profile"])
    state["stage"] = "collect_info"
    # Mark if info was just completed in this turn
    state["just_completed"] = (not was_complete_before) and state["is_info_complete"]
    return state


def search_knowledge_base(state: TutorState) -> TutorState:
    """
    Node 2b: Search knowledge base for similar questions.
    Only searches within the current student's records.
    """
    logger.info(f"[{state['student_id']}] Stage: search_knowledge_base")
    result = kb_retriever.search(state["student_input"], student_id=state["student_id"])
    state["kb_search_result"] = result
    state["kb_hit"] = result.get("found", False)
    state["socratic_context"] = result.get("best_match")
    state["stage"] = "search_knowledge_base"
    return state


def socratic_teach(state: TutorState) -> TutorState:
    """
    Node 3a: Socratic teaching — guide student through questions.
    """
    logger.info(f"[{state['student_id']}] Stage: socratic_teach")
    result = socratic_tutor.teach(
        student_id=state["student_id"],
        student_input=state["student_input"],
        context=state["socratic_context"],
        session_id=state["session_id"],
    )
    state["final_reply"] = result["reply"]
    state["stage"] = "socratic_teach"
    return state


def tavily_search(state: TutorState) -> TutorState:
    """
    Node 3b: Search Tavily for real-time info.
    """
    logger.info(f"[{state['student_id']}] Stage: tavily_search")
    result = search_agent.search(
        student_id=state["student_id"],
        query=state["student_input"],
    )
    state["search_result"] = result.get("raw_results", [])
    state["stage"] = "tavily_search"
    return state


def generate_answer(state: TutorState) -> TutorState:
    """
    Node 4: Generate final answer from search results.
    """
    logger.info(f"[{state['student_id']}] Stage: generate_answer")
    result = search_agent.generate_answer(
        student_id=state["student_id"],
        query=state["student_input"],
        search_results=state.get("search_result", []),
        session_id=state["session_id"],
    )
    state["final_reply"] = result["reply"] + "\n\n💡 要我出一道题来检验一下你的理解吗？你可以回复「出题」或「不用了」。"
    state["stage"] = "generate_answer"
    return state


def generate_quiz(state: TutorState) -> TutorState:
    """
    Node 5: Generate a quiz question.
    """
    logger.info(f"[{state['student_id']}] Stage: generate_quiz")
    result = quiz_agent.generate_question(
        student_id=state["student_id"],
        topic=state.get("quiz_topic", state["student_input"]),
        difficulty=state.get("quiz_difficulty", "适中"),
    )
    state["quiz_question"] = result["question"]
    state["quiz_reference"] = result["reference_answer"]
    state["final_reply"] = (
        f"📚 **练习题**\n\n{result['question']}\n\n"
        f"💡 提示：{result['hint']}\n\n"
        f"请直接回复你的答案，我会帮你评判。"
    )
    state["stage"] = "generate_quiz"
    return state


def judge_answer(state: TutorState) -> TutorState:
    """
    Node 6: Judge student's quiz answer.
    """
    logger.info(f"[{state['student_id']}] Stage: judge_answer")
    result = quiz_agent.judge_answer(
        student_id=state["student_id"],
        question=state.get("quiz_question", ""),
        reference_answer=state.get("quiz_reference", ""),
        student_answer=state["student_input"],
    )
    state["quiz_judge_result"] = result
    if result["is_correct"]:
        state["final_reply"] = (
            f"✅ **回答正确！**\n\n{result['evaluation']}\n\n"
            f"{result['encouragement']}\n\n"
            f"想挑战更难的题目吗？回复「更难」或「结束」。"
        )
    else:
        state["final_reply"] = (
            f"❌ **回答有误**\n\n{result['evaluation']}\n\n"
            f"{result['encouragement']}\n\n"
            f"你可以：\n"
            f"1. 回复「引导」—— 我会用苏格拉底提问法一步步引导你\n"
            f"2. 回复「答案」—— 我直接告诉你正确答案\n"
            f"3. 回复「结束」—— 回到正常问答"
        )
    state["stage"] = "judge_answer"
    return state


def quiz_socratic(state: TutorState) -> TutorState:
    """
    Node 7: Socratic guidance for wrong quiz answer.
    """
    logger.info(f"[{state['student_id']}] Stage: quiz_socratic")
    result = quiz_agent.socratic_guide(
        student_id=state["student_id"],
        question=state.get("quiz_question", ""),
        reference_answer=state.get("quiz_reference", ""),
        student_answer=state.get("quiz_student_answer", ""),
    )
    state["final_reply"] = (
        f"🤔 **引导思考**\n\n{result['reply']}\n\n"
        f"想好了可以回复你的新答案，或者回复「答案」直接查看正确解答。"
    )
    state["stage"] = "quiz_socratic"
    return state


def quiz_direct_answer(state: TutorState) -> TutorState:
    """
    Node 8: Direct answer for quiz.
    """
    logger.info(f"[{state['student_id']}] Stage: quiz_direct_answer")
    result = quiz_agent.direct_answer(
        student_id=state["student_id"],
        question=state.get("quiz_question", ""),
        reference_answer=state.get("quiz_reference", ""),
        student_answer=state.get("quiz_student_answer", ""),
    )
    state["final_reply"] = (
        f"{result['reply']}\n\n"
        f"还想继续练习吗？回复「出题」或「结束」。"
    )
    state["stage"] = "quiz_direct_answer"
    return state


# ── Conditional routing ──────────────────────────────────────────────

def route_after_check(state: TutorState) -> Literal["collect_info", "search_knowledge_base"]:
    """After checking info: if incomplete, collect; else search KB."""
    if state["is_info_complete"]:
        return "search_knowledge_base"
    return "collect_info"


def route_after_collect(state: TutorState) -> Literal["__end__", "search_knowledge_base"]:
    """After collecting info: if still incomplete, end (ask more).
    If just completed in this turn, end with confirmation (don't treat as question)."""
    if state.get("just_completed", False):
        # Info was just completed — return confirmation, don't search KB
        return "__end__"
    if state["is_info_complete"]:
        return "search_knowledge_base"
    return "__end__"


def route_after_kb_search(state: TutorState) -> Literal["socratic_teach", "tavily_search"]:
    """After KB search: if hit, use Socratic; else use Tavily."""
    if state["kb_hit"]:
        return "socratic_teach"
    return "tavily_search"


def route_after_answer(state: TutorState) -> Literal["__end__", "generate_quiz"]:
    """After generating answer: check if student wants a quiz."""
    mode = state.get("mode", "chat")
    if mode == "quiz_question":
        return "generate_quiz"
    return "__end__"


def route_after_quiz(state: TutorState) -> Literal["judge_answer", "__end__"]:
    """After generating quiz: student answers or exits."""
    mode = state.get("mode", "chat")
    if mode == "quiz_answer":
        return "judge_answer"
    return "__end__"


def route_after_judge(state: TutorState) -> Literal["quiz_socratic", "quiz_direct_answer", "generate_quiz", "__end__"]:
    """After judging answer: guide, direct answer, harder quiz, or end."""
    mode = state.get("mode", "chat")
    if mode == "quiz_socratic":
        return "quiz_socratic"
    if mode == "quiz_direct":
        return "quiz_direct_answer"
    if mode == "quiz_question":
        return "generate_quiz"
    return "__end__"


# ── Build workflow ───────────────────────────────────────────────────

def build_workflow() -> StateGraph:
    """Build the LangGraph StateGraph for TutorMind."""
    workflow = StateGraph(TutorState)

    # Add nodes
    workflow.add_node("check_student_info", check_student_info)
    workflow.add_node("collect_info", collect_info)
    workflow.add_node("search_knowledge_base", search_knowledge_base)
    workflow.add_node("socratic_teach", socratic_teach)
    workflow.add_node("tavily_search", tavily_search)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("generate_quiz", generate_quiz)
    workflow.add_node("judge_answer", judge_answer)
    workflow.add_node("quiz_socratic", quiz_socratic)
    workflow.add_node("quiz_direct_answer", quiz_direct_answer)

    # Set entry point
    workflow.set_entry_point("check_student_info")

    # Add conditional edges
    workflow.add_conditional_edges(
        "check_student_info",
        route_after_check,
        {"collect_info": "collect_info", "search_knowledge_base": "search_knowledge_base"},
    )
    workflow.add_conditional_edges(
        "collect_info",
        route_after_collect,
        {"__end__": END, "search_knowledge_base": "search_knowledge_base"},
    )
    workflow.add_conditional_edges(
        "search_knowledge_base",
        route_after_kb_search,
        {"socratic_teach": "socratic_teach", "tavily_search": "tavily_search"},
    )
    workflow.add_conditional_edges(
        "generate_answer",
        route_after_answer,
        {"__end__": END, "generate_quiz": "generate_quiz"},
    )
    workflow.add_conditional_edges(
        "generate_quiz",
        route_after_quiz,
        {"judge_answer": "judge_answer", "__end__": END},
    )
    workflow.add_conditional_edges(
        "judge_answer",
        route_after_judge,
        {
            "quiz_socratic": "quiz_socratic",
            "quiz_direct_answer": "quiz_direct_answer",
            "generate_quiz": "generate_quiz",
            "__end__": END,
        },
    )

    # Direct edges
    workflow.add_edge("socratic_teach", END)
    workflow.add_edge("tavily_search", "generate_answer")
    workflow.add_edge("quiz_socratic", END)
    workflow.add_edge("quiz_direct_answer", END)

    return workflow


def create_tutor_graph() -> StateGraph:
    """
    Create and compile the tutor graph with memory checkpointing.
    """
    workflow = build_workflow()
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
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
from app.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)

# ── Agent instances ──────────────────────────────────────────────────

info_collector = InfoCollectorAgent()
kb_retriever = KnowledgeRetrieverAgent()
socratic_tutor = SocraticTutorAgent()
search_agent = SearchAgent()
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
    """
    logger.info(f"[{state['student_id']}] Stage: search_knowledge_base")
    result = kb_retriever.search(state["student_input"])
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
    state["final_reply"] = result["reply"]
    state["stage"] = "generate_answer"
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

    # Direct edges to END
    workflow.add_edge("socratic_teach", END)
    workflow.add_edge("tavily_search", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow


def create_tutor_graph() -> StateGraph:
    """
    Create and compile the tutor graph with memory checkpointing.
    """
    workflow = build_workflow()
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
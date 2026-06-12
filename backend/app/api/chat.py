"""
Chat API endpoints with streaming support and quiz mode.
"""

import logging
import json
import asyncio
from typing import cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.graph.state import TutorState
from app.graph.workflow import create_tutor_graph
from app.agents.orchestrator import get_orchestrator
from app.models.database import init_db
from app.memory.long_term import LongTermMemory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize DB on first request
init_db()

# Initialize the graph once
tutor_graph = create_tutor_graph()
orchestrator = get_orchestrator()


# ── Mode detection ───────────────────────────────────────────────────

_QUIZ_KEYWORDS = ["出题", "考我", "练习", "做题", "测试", "quiz", "exercise"]
_DIFFICULTY_KEYWORDS = {
    "简单": ["简单", "容易", "基础"],
    "适中": ["适中", "一般", "普通"],
    "困难": ["难", "困难", "挑战", "高级"],
}


def _detect_mode(student_input: str, prev_state: dict | None) -> tuple[str, dict]:
    """
    Detect interaction mode from student input.
    Returns (mode, extra_state).
    """
    text = student_input.strip().lower()

    # If previous state exists and we're in quiz mode
    if prev_state:
        prev_mode = prev_state.get("mode", "chat")

        # Previous turn was quiz_question → student is answering
        if prev_mode == "quiz_question":
            return "quiz_answer", {
                "quiz_student_answer": student_input,
                "quiz_question": prev_state.get("quiz_question", ""),
                "quiz_reference": prev_state.get("quiz_reference", ""),
                "quiz_topic": prev_state.get("quiz_topic", ""),
            }

        # Previous turn was generate_quiz → student is answering the quiz
        if prev_mode == "generate_quiz":
            return "quiz_answer", {
                "quiz_student_answer": student_input,
                "quiz_question": prev_state.get("quiz_question", ""),
                "quiz_reference": prev_state.get("quiz_reference", ""),
                "quiz_topic": prev_state.get("quiz_topic", ""),
            }

        # Previous turn was judge_answer → student is choosing follow-up
        if prev_mode == "judge_answer":
            # Check what student chose
            if any(k in text for k in ["1", "引导", "一步步", "思考"]):
                return "quiz_socratic", {
                    "quiz_question": prev_state.get("quiz_question", ""),
                    "quiz_reference": prev_state.get("quiz_reference", ""),
                    "quiz_student_answer": prev_state.get("quiz_student_answer", ""),
                    "quiz_topic": prev_state.get("quiz_topic", ""),
                }
            elif any(k in text for k in ["2", "直接", "答案", "告诉"]):
                return "quiz_direct", {
                    "quiz_question": prev_state.get("quiz_question", ""),
                    "quiz_reference": prev_state.get("quiz_reference", ""),
                    "quiz_student_answer": prev_state.get("quiz_student_answer", ""),
                    "quiz_topic": prev_state.get("quiz_topic", ""),
                }
            elif any(k in text for k in ["3", "简单", "换"]):
                return "quiz_question", {
                    "quiz_topic": prev_state.get("quiz_topic", ""),
                    "quiz_difficulty": "简单",
                }
            elif any(k in text for k in ["更难的", "挑战", "难"]):
                return "quiz_question", {
                    "quiz_topic": prev_state.get("quiz_topic", ""),
                    "quiz_difficulty": "困难",
                }
            elif any(k in text for k in ["结束", "继续提问", "不练"]):
                return "chat", {}

        # Previous turn was quiz_socratic or quiz_direct → student may want more
        if prev_mode in ("quiz_socratic", "quiz_direct"):
            if any(k in text for k in _QUIZ_KEYWORDS):
                return "quiz_question", {"quiz_topic": prev_state.get("quiz_topic", "")}
            return "chat", {}

    # Fresh quiz request
    if any(k in text for k in _QUIZ_KEYWORDS):
        # Extract topic from input (remove quiz keywords)
        topic = student_input
        for kw in _QUIZ_KEYWORDS:
            topic = topic.replace(kw, "").replace(kw.lower(), "")
        topic = topic.strip(" ，。！？")
        if not topic:
            topic = "数学"  # default

        # Detect difficulty
        difficulty = "适中"
        for diff, keywords in _DIFFICULTY_KEYWORDS.items():
            if any(k in text for k in keywords):
                difficulty = diff
                break

        return "quiz_question", {"quiz_topic": topic, "quiz_difficulty": difficulty}

    return "chat", {}


# ── Non-streaming chat ───────────────────────────────────────────────

@router.post(
    "/",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}},
)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message to the tutor and get a response."""
    try:
        # Detect mode
        mode, extra = _detect_mode(req.message, None)

        # Direct quiz modes bypass the graph
        if mode == "quiz_question":
            from app.agents.quiz_agent import QuizAgent
            quiz_agent = QuizAgent()
            quiz_result = quiz_agent.generate_question(
                student_id=req.student_id,
                topic=extra.get("quiz_topic", req.message),
                difficulty=extra.get("quiz_difficulty", "适中"),
            )
            reply = (
                f"📚 **练习题**\n\n{quiz_result['question']}\n\n"
                f"💡 提示：{quiz_result['hint']}\n\n"
                f"请直接回复你的答案，我会帮你评判。"
            )
            orchestrator.save_conversation_turn(
                student_id=req.student_id,
                session_id=req.session_id,
                student_input=req.message,
                assistant_reply=reply,
                agent_name="generate_quiz",
            )
            return ChatResponse(
                student_id=req.student_id,
                session_id=req.session_id,
                reply=reply,
                agent_name="generate_quiz",
                stage="generate_quiz",
                is_guided=False,
                metadata={"mode": "quiz_question"},
            )

        if mode == "quiz_answer":
            from app.agents.quiz_agent import QuizAgent
            quiz_agent = QuizAgent()
            judge_result = quiz_agent.judge_answer(
                student_id=req.student_id,
                question=extra.get("quiz_question", ""),
                reference_answer=extra.get("quiz_reference", ""),
                student_answer=req.message,
            )
            if judge_result["is_correct"]:
                reply = (
                    f"✅ **回答正确！**\n\n{judge_result['evaluation']}\n\n"
                    f"{judge_result['encouragement']}\n\n"
                    f"想挑战更难的题目吗？回复「更难」或「结束」。"
                )
            else:
                reply = (
                    f"❌ **回答有误**\n\n{judge_result['evaluation']}\n\n"
                    f"{judge_result['encouragement']}\n\n"
                    f"你可以：\n"
                    f"1. 回复「引导」—— 我会用苏格拉底提问法一步步引导你\n"
                    f"2. 回复「答案」—— 我直接告诉你正确答案\n"
                    f"3. 回复「结束」—— 回到正常问答"
                )
            orchestrator.save_conversation_turn(
                student_id=req.student_id,
                session_id=req.session_id,
                student_input=req.message,
                assistant_reply=reply,
                agent_name="judge_answer",
            )
            return ChatResponse(
                student_id=req.student_id,
                session_id=req.session_id,
                reply=reply,
                agent_name="judge_answer",
                stage="judge_answer",
                is_guided=False,
                metadata={"mode": "quiz_answer", "is_correct": judge_result["is_correct"]},
            )

        if mode == "quiz_socratic":
            from app.agents.quiz_agent import QuizAgent
            quiz_agent = QuizAgent()
            guide_result = quiz_agent.socratic_guide(
                student_id=req.student_id,
                question=extra.get("quiz_question", ""),
                reference_answer=extra.get("quiz_reference", ""),
                student_answer=extra.get("quiz_student_answer", ""),
            )
            reply = (
                f"🤔 **引导思考**\n\n{guide_result['reply']}\n\n"
                f"想好了可以回复你的新答案，或者回复「答案」直接查看正确解答。"
            )
            orchestrator.save_conversation_turn(
                student_id=req.student_id,
                session_id=req.session_id,
                student_input=req.message,
                assistant_reply=reply,
                agent_name="quiz_socratic",
            )
            return ChatResponse(
                student_id=req.student_id,
                session_id=req.session_id,
                reply=reply,
                agent_name="quiz_socratic",
                stage="quiz_socratic",
                is_guided=False,
                metadata={"mode": "quiz_socratic"},
            )

        if mode == "quiz_direct":
            from app.agents.quiz_agent import QuizAgent
            quiz_agent = QuizAgent()
            answer_result = quiz_agent.direct_answer(
                student_id=req.student_id,
                question=extra.get("quiz_question", ""),
                reference_answer=extra.get("quiz_reference", ""),
                student_answer=extra.get("quiz_student_answer", ""),
            )
            reply = (
                f"{answer_result['reply']}\n\n"
                f"还想继续练习吗？回复「出题」或「结束」。"
            )
            orchestrator.save_conversation_turn(
                student_id=req.student_id,
                session_id=req.session_id,
                student_input=req.message,
                assistant_reply=reply,
                agent_name="quiz_direct_answer",
            )
            return ChatResponse(
                student_id=req.student_id,
                session_id=req.session_id,
                reply=reply,
                agent_name="quiz_direct_answer",
                stage="quiz_direct_answer",
                is_guided=False,
                metadata={"mode": "quiz_direct"},
            )

        initial_state: TutorState = {
            "student_id": req.student_id,
            "session_id": req.session_id,
            "student_input": req.message,
            "student_profile": None,
            "is_info_complete": False,
            "just_completed": False,
            "mode": mode,
            "quiz_topic": extra.get("quiz_topic", ""),
            "quiz_difficulty": extra.get("quiz_difficulty", "适中"),
            "quiz_question": extra.get("quiz_question", ""),
            "quiz_reference": extra.get("quiz_reference", ""),
            "quiz_student_answer": extra.get("quiz_student_answer", ""),
            "quiz_judge_result": None,
            "stage": "start",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }

        config = {"configurable": {"thread_id": req.session_id}}
        result = tutor_graph.invoke(initial_state, config=config)
        final_state = cast(TutorState, result)

        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])

        orchestrator.save_conversation_turn(
            student_id=req.student_id,
            session_id=req.session_id,
            student_input=req.message,
            assistant_reply=final_state["final_reply"],
            agent_name=final_state["stage"],
        )

        # After graph execution, rebuild short-term memory for this session from DB
        # so that each session only sees its own history.
        from app.memory.short_term import ShortTermMemory
        from app.memory.long_term import LongTermMemory
        stm = ShortTermMemory()
        ltm = LongTermMemory()
        db_msgs = ltm.get_session_messages(req.session_id, limit=20)
        stm.clear(req.session_id)
        for msg in db_msgs:
            stm.add(req.session_id, msg["role"], msg["content"])

        return ChatResponse(
            student_id=req.student_id,
            session_id=req.session_id,
            reply=final_state["final_reply"],
            agent_name=final_state["stage"],
            stage=final_state["stage"],
            is_guided=final_state["kb_hit"],
            metadata={
                "kb_hit": final_state["kb_hit"],
                "is_weak_foundation": final_state["is_weak_foundation"],
                "mode": final_state.get("mode", "chat"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat pipeline error")
        raise HTTPException(status_code=500, detail=str(e))


# ── Streaming chat ───────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """Send a message and receive a streaming response via SSE."""
    async def event_generator():
        try:
            # Detect mode
            mode, extra = _detect_mode(req.message, None)

            initial_state: TutorState = {
                "student_id": req.student_id,
                "session_id": req.session_id,
                "student_input": req.message,
                "student_profile": None,
                "is_info_complete": False,
                "just_completed": False,
                "mode": mode,
                "quiz_topic": extra.get("quiz_topic", ""),
                "quiz_difficulty": extra.get("quiz_difficulty", "适中"),
                "quiz_question": extra.get("quiz_question", ""),
                "quiz_reference": extra.get("quiz_reference", ""),
                "quiz_student_answer": extra.get("quiz_student_answer", ""),
                "quiz_judge_result": None,
                "stage": "start",
                "kb_search_result": None,
                "kb_hit": False,
                "socratic_context": None,
                "search_result": None,
                "final_reply": "",
                "is_weak_foundation": False,
                "messages": [],
                "error": None,
            }

            # If mode is quiz_question, skip normal pipeline and go directly to generate_quiz
            if mode == "quiz_question":
                from app.agents.quiz_agent import QuizAgent
                quiz_agent = QuizAgent()
                quiz_result = quiz_agent.generate_question(
                    student_id=req.student_id,
                    topic=extra.get("quiz_topic", req.message),
                    difficulty=extra.get("quiz_difficulty", "适中"),
                )
                reply = (
                    f"📚 **练习题**\n\n{quiz_result['question']}\n\n"
                    f"💡 提示：{quiz_result['hint']}\n\n"
                    f"请直接回复你的答案，我会帮你评判。"
                )

                yield f"data: {json.dumps({'type': 'meta', 'agent_name': 'generate_quiz', 'stage': 'generate_quiz', 'is_guided': False})}\n\n"

                chunk_size = 2
                for i in range(0, len(reply), chunk_size):
                    chunk = reply[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                orchestrator.save_conversation_turn(
                    student_id=req.student_id,
                    session_id=req.session_id,
                    student_input=req.message,
                    assistant_reply=reply,
                    agent_name="generate_quiz",
                )
                return

            # If mode is quiz_answer, judge the answer directly
            if mode == "quiz_answer":
                from app.agents.quiz_agent import QuizAgent
                quiz_agent = QuizAgent()
                judge_result = quiz_agent.judge_answer(
                    student_id=req.student_id,
                    question=extra.get("quiz_question", ""),
                    reference_answer=extra.get("quiz_reference", ""),
                    student_answer=req.message,
                )
                if judge_result["is_correct"]:
                    reply = (
                        f"✅ **回答正确！**\n\n{judge_result['evaluation']}\n\n"
                        f"{judge_result['encouragement']}\n\n"
                        f"想挑战更难的题目吗？回复「更难」或「结束」。"
                    )
                    agent_name = "judge_answer"
                else:
                    reply = (
                        f"❌ **回答有误**\n\n{judge_result['evaluation']}\n\n"
                        f"{judge_result['encouragement']}\n\n"
                        f"你可以：\n"
                        f"1. 回复「引导」—— 我会用苏格拉底提问法一步步引导你\n"
                        f"2. 回复「答案」—— 我直接告诉你正确答案\n"
                        f"3. 回复「结束」—— 回到正常问答"
                    )
                    agent_name = "judge_answer"

                yield f"data: {json.dumps({'type': 'meta', 'agent_name': agent_name, 'stage': agent_name, 'is_guided': False})}\n\n"

                chunk_size = 2
                for i in range(0, len(reply), chunk_size):
                    chunk = reply[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                orchestrator.save_conversation_turn(
                    student_id=req.student_id,
                    session_id=req.session_id,
                    student_input=req.message,
                    assistant_reply=reply,
                    agent_name=agent_name,
                )
                return

            # If mode is quiz_socratic, provide Socratic guidance
            if mode == "quiz_socratic":
                from app.agents.quiz_agent import QuizAgent
                quiz_agent = QuizAgent()
                guide_result = quiz_agent.socratic_guide(
                    student_id=req.student_id,
                    question=extra.get("quiz_question", ""),
                    reference_answer=extra.get("quiz_reference", ""),
                    student_answer=extra.get("quiz_student_answer", ""),
                )
                reply = (
                    f"🤔 **引导思考**\n\n{guide_result['reply']}\n\n"
                    f"想好了可以回复你的新答案，或者回复「答案」直接查看正确解答。"
                )
                agent_name = "quiz_socratic"

                yield f"data: {json.dumps({'type': 'meta', 'agent_name': agent_name, 'stage': agent_name, 'is_guided': False})}\n\n"

                chunk_size = 2
                for i in range(0, len(reply), chunk_size):
                    chunk = reply[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                orchestrator.save_conversation_turn(
                    student_id=req.student_id,
                    session_id=req.session_id,
                    student_input=req.message,
                    assistant_reply=reply,
                    agent_name=agent_name,
                )
                return

            # If mode is quiz_direct, give direct answer
            if mode == "quiz_direct":
                from app.agents.quiz_agent import QuizAgent
                quiz_agent = QuizAgent()
                answer_result = quiz_agent.direct_answer(
                    student_id=req.student_id,
                    question=extra.get("quiz_question", ""),
                    reference_answer=extra.get("quiz_reference", ""),
                    student_answer=extra.get("quiz_student_answer", ""),
                )
                reply = (
                    f"{answer_result['reply']}\n\n"
                    f"还想继续练习吗？回复「出题」或「结束」。"
                )
                agent_name = "quiz_direct_answer"

                yield f"data: {json.dumps({'type': 'meta', 'agent_name': agent_name, 'stage': agent_name, 'is_guided': False})}\n\n"

                chunk_size = 2
                for i in range(0, len(reply), chunk_size):
                    chunk = reply[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                orchestrator.save_conversation_turn(
                    student_id=req.student_id,
                    session_id=req.session_id,
                    student_input=req.message,
                    assistant_reply=reply,
                    agent_name=agent_name,
                )
                return

            config = {"configurable": {"thread_id": req.session_id}}
            result = tutor_graph.invoke(initial_state, config=config)
            final_state = cast(TutorState, result)

            # After graph execution, load current session history from DB into short-term memory
            # so that the next turn in this session sees the full conversation context.
            # This also ensures each session only sees its own history.
            from app.memory.short_term import ShortTermMemory
            from app.memory.long_term import LongTermMemory
            stm = ShortTermMemory()
            ltm = LongTermMemory()
            db_msgs = ltm.get_session_messages(req.session_id, limit=20)
            # Rebuild short-term buffer for this session from DB
            stm.clear(req.session_id)
            for msg in db_msgs:
                stm.add(req.session_id, msg["role"], msg["content"])

            if final_state.get("error"):
                yield f"data: {json.dumps({'type': 'error', 'content': final_state['error']})}\n\n"
                return

            reply = final_state["final_reply"]
            agent_name = final_state["stage"]

            # Send metadata
            yield f"data: {json.dumps({'type': 'meta', 'agent_name': agent_name, 'stage': final_state['stage'], 'is_guided': final_state['kb_hit']})}\n\n"

            # Stream content
            chunk_size = 2
            for i in range(0, len(reply), chunk_size):
                chunk = reply[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            orchestrator.save_conversation_turn(
                student_id=req.student_id,
                session_id=req.session_id,
                student_input=req.message,
                assistant_reply=reply,
                agent_name=agent_name,
            )

        except Exception as e:
            logger.exception("Streaming error")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Quiz-specific endpoints ──────────────────────────────────────────

@router.post("/quiz/start")
async def start_quiz(student_id: str, session_id: str, topic: str, difficulty: str = "适中"):
    """Start a quiz session on a specific topic."""
    try:
        initial_state: TutorState = {
            "student_id": student_id,
            "session_id": session_id,
            "student_input": f"出题：{topic}",
            "student_profile": None,
            "is_info_complete": True,
            "just_completed": False,
            "mode": "quiz_question",
            "quiz_topic": topic,
            "quiz_difficulty": difficulty,
            "quiz_question": "",
            "quiz_reference": "",
            "quiz_student_answer": "",
            "quiz_judge_result": None,
            "stage": "start",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }

        config = {"configurable": {"thread_id": session_id}}
        result = tutor_graph.invoke(initial_state, config=config)
        final_state = cast(TutorState, result)

        return {
            "question": final_state["quiz_question"],
            "reply": final_state["final_reply"],
        }
    except Exception as e:
        logger.exception("Quiz start error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quiz/answer")
async def submit_answer(student_id: str, session_id: str, answer: str):
    """Submit an answer to the current quiz question."""
    try:
        initial_state: TutorState = {
            "student_id": student_id,
            "session_id": session_id,
            "student_input": answer,
            "student_profile": None,
            "is_info_complete": True,
            "just_completed": False,
            "mode": "quiz_answer",
            "quiz_topic": "",
            "quiz_difficulty": "",
            "quiz_question": "",
            "quiz_reference": "",
            "quiz_student_answer": answer,
            "quiz_judge_result": None,
            "stage": "start",
            "kb_search_result": None,
            "kb_hit": False,
            "socratic_context": None,
            "search_result": None,
            "final_reply": "",
            "is_weak_foundation": False,
            "messages": [],
            "error": None,
        }

        config = {"configurable": {"thread_id": session_id}}
        result = tutor_graph.invoke(initial_state, config=config)
        final_state = cast(TutorState, result)

        return {
            "is_correct": final_state.get("quiz_judge_result", {}).get("is_correct", False),
            "evaluation": final_state.get("quiz_judge_result", {}).get("evaluation", ""),
            "reply": final_state["final_reply"],
        }
    except Exception as e:
        logger.exception("Quiz answer error")
        raise HTTPException(status_code=500, detail=str(e))


# ── History & Sessions ───────────────────────────────────────────────

@router.get("/history/{student_id}/{session_id}")
async def get_chat_history(student_id: str, session_id: str):
    """Get chat history for a specific session."""
    try:
        lt = LongTermMemory()
        messages = lt.get_session_messages(session_id, limit=100)
        return {
            "student_id": student_id,
            "session_id": session_id,
            "messages": messages,
        }
    except Exception as e:
        logger.exception("Get history error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{student_id}")
async def get_student_sessions(student_id: str):
    """Get all sessions for a student."""
    try:
        from app.models.database import get_db
        with get_db() as db:
            rows = db.execute(
                "SELECT session_id, created_at, is_active, title FROM sessions WHERE student_id = ? ORDER BY created_at DESC",
                (student_id,),
            ).fetchall()
        sessions = []
        for r in rows:
            sess = dict(r)
            sessions.append(sess)
        return {
            "student_id": student_id,
            "sessions": sessions,
        }
    except Exception as e:
        logger.exception("Get sessions error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_session/{student_id}")
async def create_session(student_id: str) -> dict:
    """Create a brand new chat session for a student."""
    lt = LongTermMemory()
    session_id = lt.create_new_session(student_id)
    return {"student_id": student_id, "session_id": session_id}


@router.delete("/session/{student_id}/{session_id}")
async def delete_session(student_id: str, session_id: str):
    """Delete a chat session and its messages."""
    try:
        from app.models.database import get_db
        from app.memory.short_term import ShortTermMemory
        from app.memory.long_term import LongTermMemory

        with get_db() as db:
            # Delete messages first (foreign key constraint if added later)
            db.execute(
                "DELETE FROM messages WHERE session_id = ? AND student_id = ?",
                (session_id, student_id),
            )
            # Delete the session
            db.execute(
                "DELETE FROM sessions WHERE session_id = ? AND student_id = ?",
                (session_id, student_id),
            )
            db.commit()

        # Clear in-memory short-term buffer for this session
        ShortTermMemory().clear(session_id)

        return {"student_id": student_id, "session_id": session_id, "deleted": True}
    except Exception as e:
        logger.exception("Delete session error")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/message/{student_id}/{session_id}/{message_id}")
async def delete_message(student_id: str, session_id: str, message_id: str):
    """Delete a single message from a session."""
    try:
        from app.models.database import get_db
        from app.memory.short_term import ShortTermMemory
        from app.memory.long_term import LongTermMemory

        with get_db() as db:
            # Find the message by session_id + created_at (used as message_id in frontend)
            row = db.execute(
                """SELECT id FROM messages
                   WHERE session_id = ? AND student_id = ? AND created_at = ?""",
                (session_id, student_id, message_id),
            ).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Message not found")

            db.execute(
                "DELETE FROM messages WHERE id = ?",
                (row["id"],),
            )
            db.commit()

        # Rebuild short-term memory for this session from DB
        stm = ShortTermMemory()
        ltm = LongTermMemory()
        db_msgs = ltm.get_session_messages(session_id, limit=20)
        stm.clear(session_id)
        for msg in db_msgs:
            stm.add(session_id, msg["role"], msg["content"])

        return {"student_id": student_id, "session_id": session_id, "message_id": message_id, "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Delete message error")
        raise HTTPException(status_code=500, detail=str(e))
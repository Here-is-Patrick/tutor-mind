"""
Chat API endpoints with streaming support.
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


# ── Non-streaming chat ───────────────────────────────────────────────

@router.post(
    "/",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}},
)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message to the tutor and get a response."""
    try:
        # Check if we should continue a Socratic loop based on recent messages
        in_socratic_loop = False
        try:
            lt = LongTermMemory()
            recent = lt.get_session_messages(req.session_id, limit=5)
            if len(recent) >= 2:
                last_assistant = None
                for m in reversed(recent):
                    if m["role"] == "assistant" and m.get("agent_name") == "socratic_tutor":
                        last_assistant = m
                        break
                if last_assistant:
                    last_student = None
                    for m in reversed(recent):
                        if m["role"] == "student":
                            last_student = m
                            break
                    if last_student and last_student["content"] == req.message:
                        in_socratic_loop = True
        except Exception:
            pass

        initial_state: TutorState = {
            "student_id": req.student_id,
            "session_id": req.session_id,
            "student_input": req.message,
            "student_profile": None,
            "is_info_complete": False,
            "just_completed": False,
            "mode": "chat",
            "quiz_topic": "",
            "quiz_difficulty": "适中",
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
            "in_socratic_loop": in_socratic_loop,
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
            # Check if we should continue a Socratic loop based on recent messages
            in_socratic_loop = False
            try:
                lt = LongTermMemory()
                recent = lt.get_session_messages(req.session_id, limit=5)
                if len(recent) >= 2:
                    last_assistant = None
                    for m in reversed(recent):
                        if m["role"] == "assistant" and m.get("agent_name") == "socratic_tutor":
                            last_assistant = m
                            break
                    if last_assistant:
                        last_student = None
                        for m in reversed(recent):
                            if m["role"] == "student":
                                last_student = m
                                break
                        if last_student and last_student["content"] == req.message:
                            # The last assistant was socratic_tutor and this is the student's reply
                            in_socratic_loop = True
            except Exception:
                pass

            initial_state: TutorState = {
                "student_id": req.student_id,
                "session_id": req.session_id,
                "student_input": req.message,
                "student_profile": None,
                "is_info_complete": False,
                "just_completed": False,
                "mode": "chat",
                "quiz_topic": "",
                "quiz_difficulty": "适中",
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
                "in_socratic_loop": in_socratic_loop,
            }

            config = {"configurable": {"thread_id": req.session_id}}
            result = tutor_graph.invoke(initial_state, config=config)
            final_state = cast(TutorState, result)

            # After graph execution, load current session history from DB into short-term memory
            # so that the next turn in this session sees the full conversation context.
            # This also ensures each session only sees its own history.
            from app.memory.short_term import ShortTermMemory
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
            yield f"data: {json.dumps({'type': 'meta', 'agent_name': agent_name, 'stage': final_state['stage'], 'is_guided': final_state['kb_hit'], 'mode': final_state.get('mode', 'chat')})}\n\n"

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

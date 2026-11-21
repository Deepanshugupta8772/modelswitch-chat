"""Chat and session history routes for Phase 2."""

import logging
import time

from fastapi import APIRouter, HTTPException

from .config import get_settings
from .db import get_session_messages, save_exchange
from .llm import generate_reply
from .schemas import ChatMetadata, ChatRequest, ChatResponse, SessionMessagesResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    started_at = time.perf_counter()
    settings = get_settings()
    history = get_session_messages(request.session_id)
    messages = [{"role": "system", "content": settings.default_system_prompt}]
    messages.extend(
        {"role": item["role"], "content": item["content"]} for item in history
    )
    messages.append({"role": "user", "content": request.message})

    try:
        result = await generate_reply(messages)
    except Exception as exc:
        logger.warning("LLM inference failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502, detail="LLM provider request failed"
        ) from None
    latency_ms = int((time.perf_counter() - started_at) * 1000)

    metadata = ChatMetadata(
        resolution_source="LIVE_INFERENCE",
        model=settings.llm_model,
        latency_ms=latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        key_id="key_1",
        fallback_attempts=0,
    )
    save_exchange(
        request.session_id,
        request.message,
        result.reply,
        metadata.model_dump(),
    )
    return ChatResponse(
        session_id=request.session_id,
        reply=result.reply,
        metadata=metadata,
    )


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def session_messages(session_id: str) -> SessionMessagesResponse:
    messages = get_session_messages(session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="session not found")
    return SessionMessagesResponse(session_id=session_id, messages=messages)

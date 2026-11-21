"""Chat and session history routes for Phase 2."""

import logging
import time

from fastapi import APIRouter, Header, HTTPException

from .config import get_settings
from .db import get_session_messages, save_exchange
from .llm import LLMResult, cache_reply, generate_reply, get_cached_reply
from .schemas import ChatMetadata, ChatRequest, ChatResponse, SessionMessagesResponse
from .simulate import parse_simulated_failures

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    simulate_failure: str | None = Header(default=None, alias="X-Simulate-Failure"),
) -> ChatResponse:
    started_at = time.perf_counter()
    settings = get_settings()
    history = get_session_messages(request.session_id)
    messages = [{"role": "system", "content": settings.default_system_prompt}]
    messages.extend(
        {"role": item["role"], "content": item["content"]} for item in history
    )
    messages.append({"role": "user", "content": request.message})

    result = await get_cached_reply(settings.llm_model, messages)
    resolution_source = "LLM_CACHE"
    successful_key_id: str | None = None
    fallback_attempts = 0
    if result is None:
        resolution_source = "LIVE_INFERENCE"
        simulated_failures = parse_simulated_failures(
            simulate_failure, enabled=settings.enable_failure_simulation
        )
        for key_number, api_key in enumerate(settings.llm_api_keys, start=1):
            key_id = f"key_{key_number}"
            try:
                simulated_status = simulated_failures.get(
                    key_id, simulated_failures.get("*")
                )
                if simulated_status is not None:
                    raise RuntimeError(
                        f"Simulated provider failure ({simulated_status})"
                    )
                result = await generate_reply(messages, api_key)
                successful_key_id = key_id
                break
            except Exception as exc:
                logger.warning(
                    "LLM attempt failed for %s (%s)", key_id, type(exc).__name__
                )
                fallback_attempts += 1

        if result is None or successful_key_id is None:
            raise HTTPException(
                status_code=503, detail="all providers unavailable"
            ) from None
        await cache_reply(settings.llm_model, messages, result)

    latency_ms = int((time.perf_counter() - started_at) * 1000)

    metadata = ChatMetadata(
        resolution_source=resolution_source,
        model=settings.llm_model,
        latency_ms=latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        key_id=successful_key_id,
        fallback_attempts=fallback_attempts,
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

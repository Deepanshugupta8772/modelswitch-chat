"""LiteLLM inference and response cache for the chat backend."""

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from litellm import Cache, acompletion

from .config import get_settings


@dataclass(frozen=True)
class LLMResult:
    reply: str
    input_tokens: int
    output_tokens: int


_settings = get_settings()
_response_cache = Cache(type="local") if _settings.cache_enabled else None


def _cache_key(model: str, messages: list[dict[str, str]]) -> str:
    cache_identity = json.dumps(
        {"model": model, "messages": messages},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(cache_identity.encode("utf-8")).hexdigest()


async def get_cached_reply(
    model: str, messages: list[dict[str, str]]
) -> LLMResult | None:
    """Look up a reply using only its model and complete message list."""
    if _response_cache is None:
        return None

    cached: Any = await _response_cache.async_get_cache(
        cache_key=_cache_key(model, messages)
    )
    if not isinstance(cached, dict):
        return None
    try:
        return LLMResult(
            reply=str(cached["reply"]),
            input_tokens=int(cached["input_tokens"]),
            output_tokens=int(cached["output_tokens"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


async def cache_reply(
    model: str, messages: list[dict[str, str]], result: LLMResult
) -> None:
    """Store only a successful reply and its original per-request usage."""
    if _response_cache is None:
        return

    await _response_cache.async_add_cache(
        {
            "reply": result.reply,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
        cache_key=_cache_key(model, messages),
    )


async def generate_reply(messages: list[dict[str, str]], api_key: str) -> LLMResult:
    """Call the configured model using the supplied key for one attempt."""
    settings = get_settings()
    response: Any = await acompletion(
        model=settings.llm_model,
        messages=messages,
        api_key=api_key,
    )
    reply = response.choices[0].message.content
    usage = response.usage
    return LLMResult(
        reply=str(reply or ""),
        input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
    )

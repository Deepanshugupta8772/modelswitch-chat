"""Single-key LiteLLM inference for Phase 2."""

from dataclasses import dataclass
from typing import Any

from litellm import acompletion

from .config import get_settings


@dataclass(frozen=True)
class LLMResult:
    reply: str
    input_tokens: int
    output_tokens: int


async def generate_reply(messages: list[dict[str, str]]) -> LLMResult:
    """Call the configured model with only the first configured API key."""
    settings = get_settings()
    if not settings.llm_api_keys:
        raise RuntimeError("No LLM API key is configured")

    response: Any = await acompletion(
        model=settings.llm_model,
        messages=messages,
        api_key=settings.llm_api_keys[0],
    )
    reply = response.choices[0].message.content
    usage = response.usage
    return LLMResult(
        reply=str(reply or ""),
        input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
    )

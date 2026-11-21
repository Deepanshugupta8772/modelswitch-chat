"""Shared isolated fixtures for backend API tests."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from litellm import Cache

# Ensure tests never inherit real provider configuration from the developer's .env.
os.environ["LLM_API_KEYS"] = "test-key-one,test-key-two"
os.environ["LLM_MODEL"] = "test/fake-model"
os.environ["DEFAULT_SYSTEM_PROMPT"] = "Test system prompt"
os.environ["CACHE_ENABLED"] = "true"
os.environ["ENABLE_FAILURE_SIMULATION"] = "true"

from backend.app import llm, routes  # noqa: E402
from backend.app.config import get_settings  # noqa: E402
from backend.app.llm import LLMResult  # noqa: E402
from backend.app.main import app  # noqa: E402


class FakeProvider:
    """Deterministic substitute for LiteLLM that records prompt calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[dict[str, str]], str]] = []
        self.failed_keys: set[str] = set()

    async def __call__(self, messages: list[dict[str, str]], api_key: str) -> LLMResult:
        self.calls.append((messages, api_key))
        if api_key in self.failed_keys:
            raise RuntimeError("deterministic provider failure")
        return LLMResult(
            reply=f"reply:{messages[-1]['content']}",
            input_tokens=23,
            output_tokens=5,
        )


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give every test a fresh LiteLLM cache and safe fake provider settings."""
    monkeypatch.setenv("LLM_API_KEYS", "test-key-one,test-key-two")
    monkeypatch.setenv("LLM_MODEL", "test/fake-model")
    monkeypatch.setenv("DEFAULT_SYSTEM_PROMPT", "Test system prompt")
    monkeypatch.setenv("CACHE_ENABLED", "true")
    monkeypatch.setenv("ENABLE_FAILURE_SIMULATION", "true")
    monkeypatch.setattr(llm, "_response_cache", Cache(type="local"))


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> FakeProvider:
    fake_provider = FakeProvider()
    monkeypatch.setattr(routes, "generate_reply", fake_provider)
    return fake_provider


@pytest.fixture
def settings():
    return get_settings()

from fastapi.testclient import TestClient

from .conftest import FakeProvider


def test_cache_hit_reuses_reply_and_tokens_across_sessions(
    client: TestClient, provider: FakeProvider
) -> None:
    first = client.post(
        "/chat", json={"session_id": "cache-a", "message": "same prompt"}
    )
    calls_after_live = len(provider.calls)
    cached = client.post(
        "/chat",
        json={"session_id": "cache-b", "message": "same prompt"},
        headers={"X-Simulate-Failure": "*=429"},
    )

    assert first.status_code == cached.status_code == 200
    assert cached.json()["reply"] == first.json()["reply"]
    assert cached.json()["metadata"]["resolution_source"] == "LLM_CACHE"
    assert cached.json()["metadata"]["key_id"] is None
    assert cached.json()["metadata"]["fallback_attempts"] == 0
    assert (
        cached.json()["metadata"]["input_tokens"]
        == first.json()["metadata"]["input_tokens"]
    )
    assert (
        cached.json()["metadata"]["output_tokens"]
        == first.json()["metadata"]["output_tokens"]
    )
    assert len(provider.calls) == calls_after_live
    history = client.get("/sessions/cache-b/messages").json()["messages"]
    assert [message["role"] for message in history] == ["user", "assistant"]


def test_different_message_does_not_hit_cache(
    client: TestClient, provider: FakeProvider
) -> None:
    client.post("/chat", json={"session_id": "cache-a", "message": "original"})
    response = client.post(
        "/chat", json={"session_id": "cache-b", "message": "different"}
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert len(provider.calls) == 2


def test_failed_request_does_not_create_cache_entry(
    client: TestClient, provider: FakeProvider
) -> None:
    failure = client.post(
        "/chat",
        json={"session_id": "failed", "message": "retry this prompt"},
        headers={"X-Simulate-Failure": "*=429"},
    )
    retry = client.post(
        "/chat",
        json={"session_id": "retry", "message": "retry this prompt"},
    )

    assert failure.status_code == 503
    assert retry.status_code == 200
    assert retry.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert len(provider.calls) == 1

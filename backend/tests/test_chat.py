from fastapi.testclient import TestClient

from .conftest import FakeProvider


def test_health_contract(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "keys_configured": 2,
        "cache_enabled": True,
    }


def test_chat_happy_path_uses_config_and_returns_live_metadata(
    client: TestClient, provider: FakeProvider
) -> None:
    response = client.post(
        "/chat", json={"session_id": "happy", "message": "  hello  "}
    )

    assert response.status_code == 200
    response_body = response.json()
    assert response_body["reply"] == "reply:hello"
    metadata = response_body["metadata"]
    assert metadata["latency_ms"] is not None
    assert isinstance(metadata["latency_ms"], int)
    assert metadata["latency_ms"] >= 0
    assert metadata == {
        "resolution_source": "LIVE_INFERENCE",
        "model": "test/fake-model",
        "latency_ms": metadata["latency_ms"],
        "input_tokens": 23,
        "output_tokens": 5,
        "key_id": "key_1",
        "fallback_attempts": 0,
    }
    assert provider.calls[0][0] == [
        {"role": "system", "content": "Test system prompt"},
        {"role": "user", "content": "hello"},
    ]


def test_multi_turn_chat_sends_stored_context(
    client: TestClient, provider: FakeProvider
) -> None:
    first = client.post(
        "/chat", json={"session_id": "multi", "message": "first message"}
    )
    followup = client.post(
        "/chat", json={"session_id": "multi", "message": "follow up"}
    )

    assert first.status_code == followup.status_code == 200
    assert provider.calls[1][0] == [
        {"role": "system", "content": "Test system prompt"},
        {"role": "user", "content": "first message"},
        {"role": "assistant", "content": "reply:first message"},
        {"role": "user", "content": "follow up"},
    ]


def test_invalid_chat_input_returns_422(client: TestClient) -> None:
    blank_message = client.post(
        "/chat", json={"session_id": "invalid", "message": "   "}
    )
    missing_message = client.post("/chat", json={"session_id": "invalid"})

    assert blank_message.status_code == 422
    assert missing_message.status_code == 422

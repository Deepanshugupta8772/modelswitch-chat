from fastapi.testclient import TestClient

from .conftest import FakeProvider


def test_first_key_failure_falls_back_to_second_key(
    client: TestClient, provider: FakeProvider, settings
) -> None:
    provider.failed_keys.add(settings.llm_api_keys[0])

    response = client.post(
        "/chat", json={"session_id": "fallback", "message": "retry me"}
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["key_id"] == "key_2"
    assert response.json()["metadata"]["fallback_attempts"] == 1
    assert [call[1] for call in provider.calls] == list(settings.llm_api_keys)
    assert len(client.get("/sessions/fallback/messages").json()["messages"]) == 2


def test_all_keys_failing_returns_503_without_history(
    client: TestClient, provider: FakeProvider, settings
) -> None:
    provider.failed_keys.update(settings.llm_api_keys)

    response = client.post(
        "/chat", json={"session_id": "all-fail", "message": "no reply"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "all providers unavailable"}
    assert client.get("/sessions/all-fail/messages").status_code == 404


def test_simulated_key_failure_uses_fallback(
    client: TestClient, provider: FakeProvider
) -> None:
    response = client.post(
        "/chat",
        json={"session_id": "simulated", "message": "simulate first key"},
        headers={"X-Simulate-Failure": "key_1=429"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["key_id"] == "key_2"
    assert response.json()["metadata"]["fallback_attempts"] == 1
    assert len(provider.calls) == 1


def test_simulation_disabled_ignores_header(
    client: TestClient, provider: FakeProvider, monkeypatch
) -> None:
    monkeypatch.setenv("ENABLE_FAILURE_SIMULATION", "false")

    response = client.post(
        "/chat",
        json={"session_id": "disabled", "message": "ignore header"},
        headers={"X-Simulate-Failure": "*=429"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["key_id"] == "key_1"
    assert len(provider.calls) == 1

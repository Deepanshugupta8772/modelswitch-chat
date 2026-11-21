from fastapi.testclient import TestClient

from .conftest import FakeProvider


def test_sessions_are_isolated_and_history_is_ordered(
    client: TestClient, provider: FakeProvider
) -> None:
    client.post("/chat", json={"session_id": "session-a", "message": "alpha"})
    client.post("/chat", json={"session_id": "session-a", "message": "next"})
    client.post("/chat", json={"session_id": "session-b", "message": "beta"})

    history_a = client.get("/sessions/session-a/messages")
    history_b = client.get("/sessions/session-b/messages")

    assert [message["content"] for message in history_a.json()["messages"]] == [
        "alpha",
        "reply:alpha",
        "next",
        "reply:next",
    ]
    assert [message["content"] for message in history_b.json()["messages"]] == [
        "beta",
        "reply:beta",
    ]
    assert all(
        message["role"] != "system"
        for message in history_a.json()["messages"] + history_b.json()["messages"]
    )


def test_unknown_session_returns_404(client: TestClient) -> None:
    response = client.get("/sessions/unknown/messages")

    assert response.status_code == 404
    assert response.json() == {"detail": "session not found"}

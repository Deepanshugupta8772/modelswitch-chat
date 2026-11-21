const apiBaseUrl = import.meta.env.VITE_API_URL?.replace(/\/+$/, "");

export class ChatApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.name = "ChatApiError";
    this.status = status;
  }
}

export async function postChat({ sessionId, message }) {
  if (!apiBaseUrl) {
    throw new Error("The chat server URL is not configured.");
  }

  let response;
  try {
    response = await fetch(`${apiBaseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
  } catch {
    throw new Error("Couldn't reach the server. Check your connection and try again.");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    throw new ChatApiError(response.status, payload.detail);
  }

  return payload;
}

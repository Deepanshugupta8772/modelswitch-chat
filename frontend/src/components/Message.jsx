import React from "react";
import Metadata from "./Metadata.jsx";

export function ChatMessage({ message }) {
  if (message.role === "error") {
    return (
      <div className="message-row message-row--assistant">
        <div className="error-message" role="alert">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`message-row message-row--${message.role}`}
      data-testid={message.role === "assistant" ? "assistant-message" : undefined}
    >
      <article className={`message-bubble message-bubble--${message.role}`}>
        <p className="message-content">{message.content}</p>
        {message.role === "assistant" && message.metadata && (
          <Metadata metadata={message.metadata} />
        )}
      </article>
    </div>
  );
}

export function LoadingMessage() {
  return (
    <div className="message-row message-row--assistant">
      <div className="loading-message" role="status" aria-label="Assistant is responding">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

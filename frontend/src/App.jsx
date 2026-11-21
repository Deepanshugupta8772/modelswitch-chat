import React from "react";
import { useEffect, useRef, useState } from "react";
import Composer from "./components/Composer.jsx";
import { ChatMessage, LoadingMessage } from "./components/Message.jsx";
import { ChatApiError, postChat } from "./api.js";

const sessionId = window.crypto.randomUUID();

function readableError(error) {
  if (error instanceof ChatApiError && error.status === 422) {
    return "Message can't be empty or longer than 4000 characters. Please check it and try again.";
  }
  if (error instanceof ChatApiError && error.status === 503) {
    return "All providers are unavailable right now. Please try again in a moment.";
  }
  if (error instanceof ChatApiError) {
    return "The message couldn't be sent. Please try again.";
  }
  return error.message || "Couldn't reach the server. Please try again.";
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const chatAreaRef = useRef(null);

  useEffect(() => {
    chatAreaRef.current?.scrollTo({
      top: chatAreaRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isSending]);

  async function sendMessage() {
    const message = draft;
    if (!message.trim() || isSending) return;

    setDraft("");
    setIsSending(true);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: message.trim() },
    ]);

    try {
      const result = await postChat({ sessionId, message: message.trim() });
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.reply,
          metadata: result.metadata,
        },
      ]);
    } catch (error) {
      if (error instanceof ChatApiError && error.status === 422) {
        setDraft(message);
      }
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "error", content: readableError(error) },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand-mark" aria-hidden="true">
          <span />
          <span />
        </div>
        <div className="brand-copy">
          <h1>ModelSwitch Chat</h1>
          <p>Thoughtful answers, resilient by design</p>
        </div>
        <div className="session-chip" title={sessionId}>
          <span className="session-indicator" />
          Session <code>{sessionId.slice(0, 8)}</code>
        </div>
      </header>

      <section
        ref={chatAreaRef}
        className="chat-area"
        aria-label="Conversation"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon" aria-hidden="true">
              <span>✳</span>
            </div>
            <p className="eyebrow">A new conversation</p>
            <h2>Ask me anything.</h2>
            <p className="empty-description">
              Start with a question, an idea, or something you want to figure out.
            </p>
            <div className="suggestions" aria-label="Example prompts">
              <span>Explain a tricky idea simply</span>
              <span>Help me plan my next project</span>
            </div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isSending && <LoadingMessage />}
          </div>
        )}
      </section>

      <footer className="composer-dock">
        <Composer
          value={draft}
          onChange={setDraft}
          onSubmit={sendMessage}
          disabled={isSending}
        />
        <p className="composer-caption">
          Enter to send <span aria-hidden="true">·</span> Shift + Enter for a new line
        </p>
      </footer>
    </main>
  );
}

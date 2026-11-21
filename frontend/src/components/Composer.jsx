import React, { useEffect, useRef } from "react";

export default function Composer({ disabled, onChange, onSubmit, value }) {
  const inputRef = useRef(null);

  useEffect(() => {
    const textarea = inputRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 132)}px`;
    }
  }, [value]);

  function handleChange(event) {
    const textarea = event.currentTarget;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 132)}px`;
    onChange(textarea.value);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <form
      className="composer"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label className="sr-only" htmlFor="chat-input">
        Your message
      </label>
      <textarea
        ref={inputRef}
        id="chat-input"
        data-testid="chat-input"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Write a message..."
        rows={1}
        disabled={disabled}
        aria-describedby="composer-hint"
      />
      <button
        className="send-button"
        data-testid="send-button"
        type="submit"
        disabled={disabled || !value.trim()}
      >
        {disabled ? "Sending…" : "Send"}
      </button>
      <span id="composer-hint" className="sr-only">
        Press Enter to send. Press Shift and Enter for a new line.
      </span>
    </form>
  );
}

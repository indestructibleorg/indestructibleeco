import React, { useState, useRef, useEffect } from "react";
import { useAI } from "../hooks/useAI";

export function AIChat() {
  const { messages, isGenerating, generate } = useAI();
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;
    generate(input.trim());
    setInput("");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "1rem" }}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              marginBottom: 12,
              padding: "0.75rem 1rem",
              borderRadius: 8,
              background: msg.role === "user" ? "#dbeafe" : "#f1f5f9",
              maxWidth: "80%",
              marginLeft: msg.role === "user" ? "auto" : 0,
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: 4 }}>
              {msg.role === "user" ? "You" : "AI"}
              {msg.engine && ` · ${msg.engine}`}
              {msg.latency_ms != null && ` · ${msg.latency_ms}ms`}
            </div>
            <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
          </div>
        ))}
        {isGenerating && (
          <div style={{ padding: "0.75rem", color: "#64748b" }}>Generating...</div>
        )}
        <div ref={endRef} />
      </div>
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, padding: "1rem", borderTop: "1px solid #e2e8f0" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Send a message..."
          disabled={isGenerating}
          style={{ flex: 1, padding: "0.5rem 0.75rem", border: "1px solid #cbd5e1", borderRadius: 6, outline: "none" }}
        />
        <button
          type="submit"
          disabled={isGenerating || !input.trim()}
          style={{ padding: "0.5rem 1.5rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}
        >
          Send
        </button>
      </form>
    </div>
  );
}

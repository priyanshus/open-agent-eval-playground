"use client";

import { useState } from "react";

const CHAT_API_URL =
  process.env.NEXT_PUBLIC_CHAT_API_URL ?? "http://localhost:8080";

export default function ChatPage() {
  const [userQuery, setUserQuery] = useState("");
  const [sessionId, setSessionId] = useState(() =>
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : ""
  );
  const [thinking, setThinking] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!userQuery.trim()) return;
    setLoading(true);
    setError(null);
    setThinking("");
    setResponse("");
    try {
      const res = await fetch(`${CHAT_API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: userQuery.trim(),
          session_id: sessionId.trim() || undefined,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const thinkingText =
        typeof data === "object" && data !== null && data.thinking
          ? data.thinking
          : "";
      const responseText =
        typeof data === "string"
          ? data
          : typeof data === "object" && data !== null && data.response
            ? data.response
            : JSON.stringify(data);
      setThinking(thinkingText);
      setResponse(responseText);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100%",
        borderTop: "1px solid #ccc",
      }}
    >
      <aside
        style={{
          width: "320px",
          minWidth: "320px",
          padding: "16px",
          borderRight: "1px solid #ccc",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <label style={{ fontSize: "12px", color: "#666" }}>Session ID</label>
        <input
          type="text"
          placeholder="session_id (optional)"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          style={{
            padding: "8px",
            border: "1px solid #ccc",
            borderRadius: "4px",
            fontSize: "14px",
          }}
        />
        <label style={{ fontSize: "12px", color: "#666" }}>Your question</label>
        <textarea
          placeholder="Ask a question..."
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          rows={4}
          style={{
            padding: "8px",
            border: "1px solid #ccc",
            borderRadius: "4px",
            fontSize: "14px",
            resize: "vertical",
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          style={{
            padding: "10px 16px",
            border: "1px solid #333",
            borderRadius: "4px",
            background: "#333",
            color: "#fff",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "14px",
          }}
        >
          {loading ? "Sending..." : "Send"}
        </button>
        {error && (
          <p style={{ fontSize: "12px", color: "#c00", margin: 0 }}>{error}</p>
        )}
      </aside>
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
        }}
      >
        <div
          style={{
            padding: "12px",
            borderBottom: "1px solid #ccc",
            fontSize: "12px",
            color: "#666",
          }}
        >
          AI Response
        </div>
        <div
          style={{
            flex: 1,
            overflow: "auto",
            padding: "16px",
            fontSize: "14px",
            lineHeight: 1.5,
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {loading && "..."}
          {!loading && !thinking && !response && "Send a message to see the response."}
          {thinking ? (
            <section
              style={{
                padding: "12px 14px",
                background: "#f0f4f8",
                borderLeft: "4px solid #6b7c9e",
                borderRadius: "4px",
                fontSize: "13px",
                color: "#444",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              <strong style={{ color: "#5a6a8a", fontSize: "12px", textTransform: "uppercase" }}>
                AI Thinking
              </strong>
              <div style={{ marginTop: "6px" }}>{thinking}</div>
            </section>
          ) : null}
          {response ? (
            <section
              style={{
                padding: "12px 14px",
                background: "#fff",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontSize: "14px",
                color: "#222",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              <strong style={{ color: "#333", fontSize: "12px", textTransform: "uppercase" }}>
                Response
              </strong>
              <div style={{ marginTop: "6px" }}>{response}</div>
            </section>
          ) : null}
        </div>
      </main>
    </div>
  );
}

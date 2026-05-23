"use client";

import { useState, useRef, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem("session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("session_id", id);
  }
  return id;
}

interface Citation {
  citation: string;
  source_url: string;
  excerpt: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef<string>("");

  useEffect(() => {
    sessionId.current = getSessionId();
    fetchConversations();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function fetchConversations() {
    const sid = sessionId.current || getSessionId();
    try {
      const res = await fetch(`${API_BASE}/api/history/${sid}`);
      const data = await res.json();
      setConversations(data.conversations || []);
    } catch {}
  }

  async function loadConversation(convId: string) {
    const sid = sessionId.current;
    try {
      const res = await fetch(`${API_BASE}/api/history/${sid}/${convId}`);
      const data = await res.json();
      const msgs: Message[] = (data.messages || []).map((m: { role: "user" | "assistant"; content: string; citations?: Citation[] | string }) => ({
        role: m.role,
        content: m.content,
        citations: Array.isArray(m.citations) ? m.citations : [],
      }));
      setMessages(msgs);
      setActiveConversationId(convId);
    } catch {}
  }

  function startNewChat() {
    setMessages([]);
    setActiveConversationId(null);
  }

  async function sendMessage() {
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          session_id: sessionId.current,
          conversation_id: activeConversationId,
        }),
      });

      const data = await res.json();
      const assistantMsg: Message = {
        role: "assistant",
        content: data.answer,
        citations: data.citations || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.conversation_id && !activeConversationId) {
        setActiveConversationId(data.conversation_id);
        await fetchConversations();
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Sidebar */}
      <aside style={{
        width: 260,
        minWidth: 260,
        background: "var(--color-primary)",
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
      }}>
        <div style={{ padding: "24px 20px 16px", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20 }}>⚖️</span>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>WA Legal</div>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>Washington State Law</div>
            </div>
          </div>
        </div>

        <div style={{ padding: "12px 16px" }}>
          <button onClick={startNewChat} style={{
            width: "100%",
            padding: "8px 12px",
            background: "rgba(255,255,255,0.1)",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.2)",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 500,
            textAlign: "left",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}>
            <span>+</span> New Conversation
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "0 8px 16px" }}>
          {conversations.length > 0 && (
            <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, fontWeight: 600, padding: "8px 8px 4px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Recent
            </div>
          )}
          {conversations.map((conv) => (
            <button key={conv.id} onClick={() => loadConversation(conv.id)} style={{
              width: "100%",
              padding: "8px 10px",
              background: activeConversationId === conv.id ? "rgba(255,255,255,0.15)" : "transparent",
              color: activeConversationId === conv.id ? "#fff" : "rgba(255,255,255,0.7)",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 13,
              textAlign: "left",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "block",
              marginBottom: 2,
            }}>
              {conv.title || "Untitled"}
            </button>
          ))}
        </div>

        <div style={{ padding: "12px 16px", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11 }}>RCW Titles 1, 9, 9A</div>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--color-bg)" }}>
        {/* Disclaimer */}
        <div style={{
          background: "#FEF9C3",
          color: "#92400E",
          fontSize: 12,
          padding: "6px 20px",
          textAlign: "center",
          borderBottom: "1px solid #FDE68A",
          flexShrink: 0,
        }}>
          Legal information only — not legal advice. Always consult a licensed attorney for your specific situation.
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px 0" }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: "center", marginTop: 80, padding: "0 24px" }}>
              <div style={{ fontSize: 40, marginBottom: 16 }}>⚖️</div>
              <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--color-primary)", marginBottom: 8 }}>
                Washington State Legal Assistant
              </h1>
              <p style={{ color: "var(--color-muted)", fontSize: 15, maxWidth: 480, margin: "0 auto 32px" }}>
                Ask questions about Washington State law. Answers are grounded in RCW sections with citations.
              </p>
              <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
                {[
                  "What is assault in the fourth degree?",
                  "Can someone carry a concealed gun in WA?",
                  "What does RCW 9A.36.041 say?",
                ].map((q) => (
                  <button key={q} onClick={() => setInput(q)} style={{
                    padding: "10px 16px",
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    cursor: "pointer",
                    fontSize: 13,
                    color: "var(--color-text)",
                    maxWidth: 220,
                    textAlign: "left",
                    lineHeight: 1.4,
                  }}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ maxWidth: 760, margin: "0 auto", padding: "0 24px", display: "flex", flexDirection: "column", gap: 16 }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{ maxWidth: msg.role === "user" ? "70%" : "85%" }}>
                    <div style={{
                      padding: "12px 16px",
                      borderRadius: msg.role === "user" ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
                      background: msg.role === "user" ? "var(--color-primary)" : "var(--color-surface)",
                      color: msg.role === "user" ? "#fff" : "var(--color-text)",
                      border: msg.role === "user" ? "none" : "1px solid var(--color-border)",
                      fontSize: 15,
                      lineHeight: 1.6,
                      whiteSpace: "pre-wrap",
                    }}>
                      {msg.content}
                    </div>
                    {msg.citations && msg.citations.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8, paddingLeft: 4 }}>
                        {msg.citations.map((c) => (
                          <a
                            key={c.citation}
                            href={c.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: 12,
                              padding: "3px 10px",
                              border: "1px solid var(--color-accent)",
                              color: "var(--color-accent)",
                              borderRadius: 20,
                              textDecoration: "none",
                              background: "transparent",
                              fontWeight: 500,
                            }}
                          >
                            RCW {c.citation}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div style={{
                    padding: "12px 18px",
                    borderRadius: "20px 20px 20px 4px",
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    color: "var(--color-muted)",
                    fontSize: 15,
                  }}>
                    Searching Washington law...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <div style={{
          padding: "16px 24px",
          background: "var(--color-surface)",
          borderTop: "1px solid var(--color-border)",
          flexShrink: 0,
        }}>
          <div style={{ maxWidth: 760, margin: "0 auto", display: "flex", gap: 10, alignItems: "flex-end" }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about Washington State law..."
              rows={1}
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: 24,
                border: "1px solid var(--color-border)",
                fontSize: 15,
                fontFamily: "inherit",
                resize: "none",
                outline: "none",
                lineHeight: 1.5,
                maxHeight: 120,
                overflowY: "auto",
                color: "var(--color-text)",
                background: "var(--color-bg)",
              }}
              onInput={(e) => {
                const el = e.currentTarget;
                el.style.height = "auto";
                el.style.height = Math.min(el.scrollHeight, 120) + "px";
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              style={{
                padding: "12px 20px",
                background: loading || !input.trim() ? "var(--color-border)" : "var(--color-accent)",
                color: loading || !input.trim() ? "var(--color-muted)" : "#fff",
                border: "none",
                borderRadius: 24,
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                fontSize: 14,
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              {loading ? "..." : "Send"}
            </button>
          </div>
          <div style={{ maxWidth: 760, margin: "6px auto 0", textAlign: "center" }}>
            <span style={{ fontSize: 12, color: "var(--color-muted)" }}>
              Press Enter to send · Shift+Enter for new line
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}

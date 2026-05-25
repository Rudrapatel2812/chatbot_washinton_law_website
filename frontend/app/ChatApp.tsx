"use client";

import { useState, useRef, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);
  return isMobile;
}

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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef<string>("");
  const isMobile = useIsMobile();

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

  const msgPadding = isMobile ? "0 12px" : "0 24px";
  const userBubbleMax = isMobile ? "88%" : "70%";
  const assistantBubbleMax = isMobile ? "95%" : "85%";

  return (
    <div style={{ display: "flex", height: "100dvh", overflow: "hidden" }}>

      {/* Mobile backdrop */}
      {isMobile && sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "fixed", inset: 0,
            background: "rgba(0,0,0,0.45)",
            zIndex: 40,
          }}
        />
      )}

      {/* Sidebar */}
      <aside style={{
        width: 260,
        minWidth: 260,
        background: "var(--color-primary)",
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
        ...(isMobile ? {
          position: "fixed",
          top: 0,
          left: 0,
          height: "100%",
          zIndex: 50,
          transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
          transition: "transform 0.25s ease",
        } : {}),
      }}>
        {/* Sidebar header */}
        <div style={{ padding: "24px 20px 16px", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 22 }}>⚖️</span>
            <div style={{ flex: 1 }}>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>WA Legal</div>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>Washington State Law</div>
            </div>
            {isMobile && (
              <button
                onClick={() => setSidebarOpen(false)}
                style={{
                  background: "none", border: "none", color: "rgba(255,255,255,0.7)",
                  cursor: "pointer", fontSize: 22, padding: "4px 8px",
                  lineHeight: 1, minWidth: 44, minHeight: 44,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >✕</button>
            )}
          </div>
        </div>

        {/* New conversation button */}
        <div style={{ padding: "12px 16px" }}>
          <button
            onClick={() => { startNewChat(); setSidebarOpen(false); }}
            style={{
              width: "100%",
              padding: "10px 14px",
              background: "rgba(255,255,255,0.1)",
              color: "#fff",
              border: "1px solid rgba(255,255,255,0.2)",
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500,
              textAlign: "left",
              display: "flex",
              alignItems: "center",
              gap: 8,
              minHeight: 44,
            }}
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>+</span> New Conversation
          </button>
        </div>

        {/* Conversation list */}
        <div style={{ flex: 1, overflowY: "auto", padding: "0 8px 16px" }}>
          {conversations.length > 0 && (
            <div style={{
              color: "rgba(255,255,255,0.4)", fontSize: 11, fontWeight: 600,
              padding: "8px 8px 4px", textTransform: "uppercase", letterSpacing: "0.05em",
            }}>
              Recent
            </div>
          )}
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => { loadConversation(conv.id); setSidebarOpen(false); }}
              style={{
                width: "100%",
                padding: "10px 12px",
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
                minHeight: 44,
              }}
            >
              {conv.title || "Untitled"}
            </button>
          ))}
        </div>

        {/* Sidebar footer */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11 }}>RCW Titles 1, 9, 9A, 10, 26, 46, 49, 59</div>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--color-bg)" }}>

        {/* Mobile top bar */}
        {isMobile && (
          <div style={{
            display: "flex", alignItems: "center", gap: 12,
            background: "var(--color-primary)",
            padding: "0 16px",
            height: 52,
            flexShrink: 0,
          }}>
            <button
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
              style={{
                background: "none", border: "none", color: "#fff",
                cursor: "pointer", fontSize: 22, padding: "4px 8px",
                lineHeight: 1, minWidth: 44, minHeight: 44,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >☰</button>
            <span style={{ fontSize: 18 }}>⚖️</span>
            <span style={{ color: "#fff", fontWeight: 700, fontSize: 16 }}>WA Legal</span>
          </div>
        )}

        {/* Disclaimer banner */}
        <div style={{
          background: "#FEF9C3",
          color: "#92400E",
          fontSize: isMobile ? 11 : 12,
          padding: isMobile ? "6px 14px" : "6px 20px",
          textAlign: "center",
          borderBottom: "1px solid #FDE68A",
          flexShrink: 0,
          lineHeight: 1.4,
        }}>
          Legal information only — not legal advice. Always consult a licensed attorney for your specific situation.
        </div>

        {/* Messages / empty state */}
        <div style={{ flex: 1, overflowY: "auto", padding: isMobile ? "16px 0" : "24px 0" }}>
          {messages.length === 0 ? (
            <div style={{
              textAlign: "center",
              marginTop: isMobile ? 32 : 72,
              padding: isMobile ? "0 16px" : "0 24px",
            }}>
              <div style={{ fontSize: isMobile ? 36 : 44, marginBottom: 14 }}>⚖️</div>
              <h1 style={{
                fontSize: isMobile ? 20 : 24,
                fontWeight: 700,
                color: "var(--color-primary)",
                marginBottom: 10,
                lineHeight: 1.3,
              }}>
                Washington State Legal Assistant
              </h1>
              <p style={{
                color: "var(--color-muted)",
                fontSize: isMobile ? 14 : 15,
                maxWidth: 480,
                margin: "0 auto 28px",
                lineHeight: 1.6,
              }}>
                Ask questions about Washington State law. Answers are grounded in RCW sections with citations.
              </p>

              {/* Suggestion cards */}
              <div style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                gap: isMobile ? 10 : 12,
                justifyContent: "center",
                alignItems: isMobile ? "stretch" : "flex-start",
                maxWidth: isMobile ? "100%" : 680,
                margin: "0 auto",
              }}>
                {[
                  "How is child custody decided in Washington?",
                  "Can a landlord keep my security deposit in WA?",
                  "What is the DUI blood alcohol limit in Washington?",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    style={{
                      padding: isMobile ? "12px 16px" : "11px 16px",
                      background: "var(--color-surface)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 10,
                      cursor: "pointer",
                      fontSize: 14,
                      color: "var(--color-text)",
                      textAlign: "left",
                      lineHeight: 1.45,
                      minHeight: 44,
                      ...(isMobile ? { width: "100%" } : { maxWidth: 220, flex: "1 1 0" }),
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div style={{
              maxWidth: 760,
              margin: "0 auto",
              padding: msgPadding,
              display: "flex",
              flexDirection: "column",
              gap: 14,
            }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{ maxWidth: msg.role === "user" ? userBubbleMax : assistantBubbleMax }}>
                    <div style={{
                      padding: isMobile ? "10px 14px" : "12px 16px",
                      borderRadius: msg.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                      background: msg.role === "user" ? "var(--color-primary)" : "var(--color-surface)",
                      color: msg.role === "user" ? "#fff" : "var(--color-text)",
                      border: msg.role === "user" ? "none" : "1px solid var(--color-border)",
                      fontSize: isMobile ? 14 : 15,
                      lineHeight: 1.6,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
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
                              padding: "4px 12px",
                              border: "1px solid var(--color-accent)",
                              color: "var(--color-accent)",
                              borderRadius: 20,
                              textDecoration: "none",
                              background: "transparent",
                              fontWeight: 500,
                              minHeight: 30,
                              display: "inline-flex",
                              alignItems: "center",
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
                    borderRadius: "18px 18px 18px 4px",
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    color: "var(--color-muted)",
                    fontSize: isMobile ? 14 : 15,
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
          padding: isMobile ? "10px 12px" : "14px 24px",
          paddingBottom: isMobile
            ? "calc(10px + env(safe-area-inset-bottom, 0px))"
            : "14px",
          background: "var(--color-surface)",
          borderTop: "1px solid var(--color-border)",
          flexShrink: 0,
        }}>
          <div style={{
            maxWidth: 760,
            margin: "0 auto",
            display: "flex",
            gap: isMobile ? 8 : 10,
            alignItems: "flex-end",
          }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about Washington State law..."
              rows={1}
              style={{
                flex: 1,
                padding: isMobile ? "10px 14px" : "12px 16px",
                borderRadius: 24,
                border: "1px solid var(--color-border)",
                fontSize: 16,
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
                padding: isMobile ? "10px 18px" : "12px 22px",
                background: loading || !input.trim() ? "var(--color-border)" : "var(--color-accent)",
                color: loading || !input.trim() ? "var(--color-muted)" : "#fff",
                border: "none",
                borderRadius: 24,
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                fontSize: 14,
                fontWeight: 600,
                flexShrink: 0,
                minHeight: 44,
                minWidth: 64,
              }}
            >
              {loading ? "..." : "Send"}
            </button>
          </div>
          {!isMobile && (
            <div style={{ maxWidth: 760, margin: "5px auto 0", textAlign: "center" }}>
              <span style={{ fontSize: 12, color: "var(--color-muted)" }}>
                Press Enter to send · Shift+Enter for new line
              </span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

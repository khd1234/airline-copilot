"use client";

import { useEffect, useRef, useState } from "react";
import { streamChat, type ChatMessage } from "@/lib/chat";

type ToolStatus = { name: string; state: "running" | "done" | "failed" };
type UiMessage = ChatMessage & { tools?: ToolStatus[]; error?: string };

// Friendly labels for the status lines.
const TOOL_LABELS: Record<string, string> = {
  search_flights: "Searching flights",
  get_booking: "Looking up booking",
  get_fare_rules: "Checking fare rules",
};

function finishTool(tools: ToolStatus[], name: string, ok: boolean): ToolStatus[] {
  const next = [...tools];
  const i = next.findIndex((t) => t.name === name && t.state === "running");
  if (i >= 0) next[i] = { ...next[i], state: ok ? "done" : "failed" };
  return next;
}

export default function Home() {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Streaming events always update the LAST message (the assistant's reply).
  function updateLast(fn: (m: UiMessage) => UiMessage) {
    setMessages((prev) => prev.map((m, i) => (i === prev.length - 1 ? fn(m) : m)));
  }

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);

    // The backend is stateless, so we send the whole history every time.
    const history: ChatMessage[] = [
      ...messages.filter((m) => m.content).map(({ role, content }) => ({ role, content })),
      { role: "user", content: text },
    ];
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "", tools: [] },
    ]);

    try {
      await streamChat(history, (event) => {
        if (event.type === "token") {
          updateLast((m) => ({ ...m, content: m.content + event.text }));
        } else if (event.type === "tool_start") {
          updateLast((m) => ({
            ...m,
            tools: [...(m.tools ?? []), { name: event.name, state: "running" }],
          }));
        } else if (event.type === "tool_result") {
          updateLast((m) => ({ ...m, tools: finishTool(m.tools ?? [], event.name, event.ok) }));
        } else if (event.type === "error") {
          updateLast((m) => ({ ...m, error: event.message }));
        }
      });
    } catch (e) {
      updateLast((m) => ({ ...m, error: e instanceof Error ? e.message : "Something went wrong" }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex h-screen max-w-2xl flex-col p-4">
      <h1 className="mb-4 text-xl font-semibold">Airline Copilot</h1>

      <div className="flex-1 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-gray-500">
            Try: &ldquo;Find flights from Delhi to Mumbai tomorrow&rdquo; or &ldquo;Status of booking ABC123&rdquo;
          </p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            {m.tools?.map((t, j) => (
              <div key={j} className="mb-1 text-xs text-gray-500">
                {t.state === "running" ? "…" : t.state === "done" ? "✓" : "!"}{" "}
                {TOOL_LABELS[t.name] ?? t.name}
              </div>
            ))}
            {m.content && (
              <div
                className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-left ${
                  m.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
                }`}
              >
                {m.content}
              </div>
            )}
            {m.error && <div className="text-sm text-red-600">{m.error}</div>}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="mt-4 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about flights, bookings, fare rules..."
          className="flex-1 rounded border border-gray-300 px-3 py-2 text-gray-900"
        />
        <button
          disabled={busy}
          className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </main>
  );
}
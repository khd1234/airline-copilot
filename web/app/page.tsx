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
    <main className="flex h-dvh w-full flex-col bg-white px-5 py-4 sm:px-8 lg:px-12">
      <h1 className="mb-5 shrink-0 border-b border-slate-200 pb-4 text-lg font-semibold tracking-tight text-slate-900">
        Airline Copilot
      </h1>

      <div className="flex-1 space-y-5 overflow-y-auto py-2">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            Try: &ldquo;Find flights from Delhi to Mumbai tomorrow&rdquo; or
            &ldquo;Status of booking ABC123&rdquo;
          </p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            {m.tools?.map((t, j) => (
              <div key={j} className="mb-2 text-xs text-slate-500">
                {t.state === "running" ? "…" : t.state === "done" ? "✓" : "!"}{" "}
                {TOOL_LABELS[t.name] ?? t.name}
              </div>
            ))}

            {m.content && (
              <div
                className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-xl px-4 py-3 text-left text-sm leading-7 ${
                  m.role === "user"
                    ? "bg-slate-100 text-slate-800"
                    : "text-slate-800"
                }`}
              >
                {m.content}
              </div>
            )}

            {m.error && (
              <div className="mt-2 text-sm text-red-600">{m.error}</div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="mt-4 flex shrink-0 gap-2 rounded-xl border border-slate-300 bg-white p-2 transition focus-within:border-slate-500 focus-within:ring-2 focus-within:ring-slate-100"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about flights, bookings, fare rules..."
          className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy ? "Sending..." : "Send"}
        </button>
      </form>
    </main>
  );
}
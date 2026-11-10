"use client";

import { useEffect, useRef, useState } from "react";
import { streamChat, type ChatMessage, type FlightResult } from "@/lib/chat";

type ToolStatus = {
  name: string;
  arguments: string;
  state: "running" | "done" | "failed";
};
type UiMessage = ChatMessage & {
  tools?: ToolStatus[];
  flightResults?: FlightResult[];
  error?: string;
};

function formatFlightDateTime(value: string) {
  return new Date(value).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
  const abortControllerRef = useRef<AbortController | null>(null);

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
    const controller = new AbortController();
    abortControllerRef.current = controller;
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
            tools: [
              ...(m.tools ?? []),
              { name: event.name, arguments: event.arguments, state: "running" },
            ],
          }));
        } else if (event.type === "tool_result") {
          updateLast((m) => ({
            ...m,
            tools: finishTool(m.tools ?? [], event.name, event.ok),
            ...(event.flight_results !== undefined
              ? { flightResults: event.flight_results }
              : {}),
          }));
        } else if (event.type === "error") {
          updateLast((m) => ({ ...m, error: event.message }));
        }
      }, controller.signal);
    } catch (e) {
      if (!controller.signal.aborted) {
        updateLast((m) => ({
          ...m,
          error: e instanceof Error ? e.message : "Something went wrong",
        }));
      }
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
      setBusy(false);
    }
  }

  return (
    <main className="flex h-dvh w-full flex-col bg-white px-5 py-4 sm:px-8 lg:px-12">
      <header className="mb-5 flex shrink-0 items-center justify-between border-b border-slate-200 pb-4">
        <h1 className="text-lg font-semibold tracking-tight text-slate-900">
          Airline Copilot
        </h1>
        <button
          type="button"
          onClick={() => setMessages([])}
          disabled={busy}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          New chat
        </button>
      </header>

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
              <div
                key={j}
                title={t.arguments}
                className="mb-2 text-xs text-slate-500"
              >
                {t.state === "running" ? "…" : t.state === "done" ? "✓" : "!"}{" "}
                {TOOL_LABELS[t.name] ?? t.name}
              </div>
            ))}

            {m.flightResults !== undefined && (
              <section className="space-y-3" aria-label="Flight results">
                <h2 className="text-sm font-medium text-slate-700">
                  {m.flightResults.length > 0
                    ? `Available flights (${m.flightResults.length})`
                    : "No flights found"}
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {m.flightResults.map((flight) => (
                    <article
                      key={flight.flight_id}
                      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium text-slate-900">{flight.airline}</p>
                          <p className="text-xs text-slate-500">{flight.flight_no}</p>
                        </div>
                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                          {flight.fare_type}
                        </span>
                      </div>

                      <div className="my-5 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                        <div>
                          <p className="text-lg font-semibold text-slate-900">
                            {formatFlightDateTime(flight.departure)}
                          </p>
                          <p className="text-sm text-slate-500">{flight.origin}</p>
                        </div>
                        <span aria-hidden="true" className="text-slate-400">→</span>
                        <div className="text-right">
                          <p className="text-lg font-semibold text-slate-900">
                            {formatFlightDateTime(flight.arrival)}
                          </p>
                          <p className="text-sm text-slate-500">{flight.destination}</p>
                        </div>
                      </div>

                      <div className="flex items-end justify-between border-t border-slate-100 pt-3">
                        <p className="text-xs text-slate-500">
                          {flight.seats_left} {flight.seats_left === 1 ? "seat" : "seats"} left
                        </p>
                        <p className="text-lg font-semibold text-slate-900">
                          ₹{flight.price_inr.toLocaleString("en-IN")}
                        </p>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}

            {m.content && m.flightResults === undefined && (
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
        className="mt-4 mb-6 flex shrink-0 gap-2 rounded-xl border border-slate-300 bg-white p-2 transition focus-within:border-slate-500 focus-within:ring-2 focus-within:ring-slate-100"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about flights, bookings, fare rules..."
          className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400"
        />
        {busy ? (
          <button
            type="button"
            onClick={() => abortControllerRef.current?.abort()}
            className="rounded-lg border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        )}
      </form>
    </main>
  );
}

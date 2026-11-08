export type ChatMessage = { role: "user" | "assistant"; content: string };

// Mirrors the events the backend sends.
export type StreamEvent =
  | { type: "token"; text: string }
  | { type: "tool_start"; name: string; arguments: string }
  | { type: "tool_result"; name: string; ok: boolean }
  | { type: "done"; provider: string }
  | { type: "error"; message: string };

const API_URL = process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:8000";

export async function streamChat(
  messages: ChatMessage[],
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
) {
  const res = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Request failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Events end with a blank line. Network chunks can cut an event in half,
    // so keep the unfinished part in the buffer for the next read.
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      if (part.startsWith("data: ")) {
        onEvent(JSON.parse(part.slice(6)) as StreamEvent);
      }
    }
  }
}
import json
import logging

from .llm import chat_completion, create_stream, with_system
from .tools import TOOLS, run_tool

log = logging.getLogger("copilot.agent")

MAX_STEPS = 5


def _assistant_message(content: str, calls: list[dict]) -> dict:
    """Build the assistant's tool-request message to put back in the conversation."""
    tool_calls = []
    for c in calls:
        entry = {
            "id": c["id"],
            "type": "function",
            "function": {"name": c["name"], "arguments": c["arguments"]},
        }
        if c.get("extra"):
            entry["extra_content"] = c["extra"]  # Gemini's thought signature
        tool_calls.append(entry)
    return {"role": "assistant", "content": content or "", "tool_calls": tool_calls}


def run_agent(messages: list[dict]) -> dict:
    convo = list(messages)  # user/assistant history; system prompt added per call
    trace = []
    provider = None

    for _ in range(MAX_STEPS):
        response, provider = chat_completion(
            with_system(convo), prefer=provider, tools=TOOLS
        )
        msg = response.choices[0].message

        # No tool requested: this is the final answer.
        if not msg.tool_calls:
            return {"reply": msg.content or "", "trace": trace, "provider": provider}

        calls = [
            {
                "id": c.id,
                "name": c.function.name,
                "arguments": c.function.arguments,
                "extra": (c.model_extra or {}).get("extra_content"),
            }
            for c in msg.tool_calls
        ]
        convo.append(_assistant_message(msg.content, calls))

        for c in calls:
            result = run_tool(c["name"], c["arguments"])
            log.info("tool %s(%s) -> %s", c["name"], c["arguments"], json.dumps(result)[:150])
            trace.append(
                {"tool": c["name"], "arguments": c["arguments"], "result_preview": json.dumps(result)[:200]}
            )
            convo.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(result)})

    return {"reply": "Sorry, I couldn't complete that request.", "trace": trace, "provider": provider}


def stream_agent(messages: list[dict]):
    """Same loop as run_agent, but yields events as they happen."""
    convo = list(messages)
    provider = None

    for _ in range(MAX_STEPS):
        stream, provider = create_stream(
            with_system(convo), prefer=provider, tools=TOOLS
        )
        text = ""
        calls: dict[int, dict] = {}  # tool calls being assembled, keyed by position

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            # 1) Normal answer text: pass straight through to the user.
            if delta.content:
                text += delta.content
                yield {"type": "token", "text": delta.content}

            # 2) Tool-call fragments: collect them, run the tool after the stream ends.
            for tc in delta.tool_calls or []:
                idx = getattr(tc, "index", None)
                if idx is None:  # some providers (Gemini) omit the index
                    idx = len(calls) if (tc.id or not calls) else max(calls)
                slot = calls.setdefault(
                    idx, {"id": "", "name": "", "arguments": "", "extra": None}
                )
                if tc.id:
                    slot["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function.arguments:
                        slot["arguments"] += tc.function.arguments  # glue the pieces
                extra = (getattr(tc, "model_extra", None) or {}).get("extra_content")
                if extra:
                    slot["extra"] = extra

        # No tool requested: the answer is complete.
        if not calls:
            yield {"type": "done", "provider": provider}
            return

        call_list = [calls[i] for i in sorted(calls)]
        for i, c in enumerate(call_list):
            if not c["id"]:
                c["id"] = f"call_{i}"
        convo.append(_assistant_message(text, call_list))

        for c in call_list:
            yield {"type": "tool_start", "name": c["name"], "arguments": c["arguments"]}
            result = run_tool(c["name"], c["arguments"])
            ok = not (isinstance(result, dict) and "error" in result)
            yield {"type": "tool_result", "name": c["name"], "ok": ok}
            convo.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(result)})

    yield {"type": "error", "message": "Sorry, I couldn't complete that request."}
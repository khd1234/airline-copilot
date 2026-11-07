import json
import logging

from .llm import chat_completion, with_system
from .tools import TOOLS, run_tool

log = logging.getLogger("copilot.agent")

MAX_STEPS = 5  # safety limit so a confused model can't loop forever


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

        # Add the assistant's tool request to the conversation (built by hand,
        # so no provider-specific extra fields leak between providers).
        tool_calls = []
        for c in msg.tool_calls:
            entry = {
                "id": c.id,
                "type": "function",
                "function": {"name": c.function.name, "arguments": c.function.arguments},
            }
            # Gemini hides a "thought signature" in an extra field. It must be
            # sent back unchanged, so copy it across if it exists.
            extra = (c.model_extra or {}).get("extra_content")
            if extra:
                entry["extra_content"] = extra
            tool_calls.append(entry)

        convo.append(
            {"role": "assistant", "content": msg.content or "", "tool_calls": tool_calls}
        )

        # Run each requested tool and feed the result back.
        for call in msg.tool_calls:
            name, raw_args = call.function.name, call.function.arguments
            result = run_tool(name, raw_args)
            log.info("tool %s(%s) -> %s", name, raw_args, json.dumps(result)[:150])
            trace.append(
                {"tool": name, "arguments": raw_args, "result_preview": json.dumps(result)[:200]}
            )
            convo.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
        print("Final conversation:", json.dumps(convo, indent=2))
    return {
        "reply": "Sorry, I couldn't complete that request.",
        "trace": trace,
        "provider": provider,
    }
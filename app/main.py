import json
import logging
from typing import Literal

import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .agent import run_agent, stream_agent
from .config import ALLOWED_ORIGINS, PROVIDERS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("copilot")

app = FastAPI(title="Airline Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    # Clients may only send user/assistant. System and tool messages are server-only.
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)


def friendly_error(e: Exception) -> tuple[int, str]:
    if isinstance(e, openai.AuthenticationError):
        return 502, "LLM provider rejected the API key. Check the keys in .env."
    if isinstance(e, openai.APIConnectionError):
        return 502, "Cannot reach the LLM provider."
    if isinstance(e, openai.RateLimitError):
        return 429, "Rate limit or quota hit on the LLM providers."
    if isinstance(e, openai.NotFoundError):
        return 502, "Model not found. Check LLM_MODEL / FALLBACK_LLM_MODEL in .env."
    if isinstance(e, openai.APIStatusError):
        return 502, f"LLM provider error ({e.status_code})."
    return 500, "Unexpected server error."


@app.get("/health")
def health():
    return {
        "status": "ok",
        "providers": [{"name": p["name"], "model": p["model"]} for p in PROVIDERS],
    }


@app.post("/chat")
def chat(req: ChatRequest):
    """Agent endpoint: the model may call tools before answering."""
    messages = [m.model_dump() for m in req.messages]
    try:
        return run_agent(messages)
    except Exception as e:
        log.exception("chat failed")
        status, msg = friendly_error(e)
        raise HTTPException(status_code=status, detail=msg)


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """Streaming agent: progress events plus tokens."""
    messages = [m.model_dump() for m in req.messages]

    def event_stream():
        try:
            for event in stream_agent(messages):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            log.exception("stream failed")
            _, msg = friendly_error(e)
            yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

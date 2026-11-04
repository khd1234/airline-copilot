import json
import logging
from pathlib import Path
from typing import Literal

import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import ALLOWED_ORIGINS, LLM_MODEL
from .llm import client, with_system

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
    # Only user/assistant are accepted, so a client can't inject a system prompt.
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)


def friendly_error(e: Exception) -> tuple[int, str]:
    if isinstance(e, openai.AuthenticationError):
        return 502, "LLM provider rejected the API key. Check LLM_API_KEY in .env."
    if isinstance(e, openai.APIConnectionError):
        return 502, "Cannot reach the LLM provider. Is Ollama running / is the base URL right?"
    if isinstance(e, openai.RateLimitError):
        return 429, "Rate limit or quota hit on the LLM provider."
    if isinstance(e, openai.NotFoundError):
        return 502, f"Model '{LLM_MODEL}' not found. Check LLM_MODEL in .env."
    if isinstance(e, openai.APIStatusError):
        return 502, f"LLM provider error ({e.status_code})."
    return 500, "Unexpected server error."


@app.get("/health")
def health():
    return {"status": "ok", "model": LLM_MODEL}


@app.post("/chat")
def chat(req: ChatRequest):
    messages = [m.model_dump() for m in req.messages]
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL, messages=with_system(messages)
        )
    except Exception as e:
        log.exception("chat failed")
        status, msg = friendly_error(e)
        raise HTTPException(status_code=status, detail=msg)

    usage = response.usage
    if usage:
        log.info("tokens in=%s out=%s", usage.prompt_tokens, usage.completion_tokens)
    return {
        "reply": response.choices[0].message.content,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
    }


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    messages = [m.model_dump() for m in req.messages]

    def event_stream():
        try:
            stream = client.chat.completions.create(
                model=LLM_MODEL, messages=with_system(messages), stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            log.exception("stream failed")
            _, msg = friendly_error(e)
            # Headers are already sent, so report the error as an SSE event.
            yield f"data: {json.dumps({'error': msg})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Simple test page at http://localhost:8000/ui/test.html
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
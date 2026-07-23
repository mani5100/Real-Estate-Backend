# ── Request / Response Schemas ───────────────────────────────────────────────

from pydantic import BaseModel
from typing import Literal, Any


class ToolCallResponse(BaseModel):
    type: Literal["tool_call"]
    tool: str
    args: dict[str, Any] = {}


class TextResponse(BaseModel):
    type: Literal["text"]
    message: str


class ConversationMessage(BaseModel):
    role: Literal["agent", "assistant", "tool_result"]
    content: str


class ChatRequest(BaseModel):
    message: str | None = None
    history: list[ConversationMessage] = []
    is_greeting: bool = False


class ChatResponse(BaseModel):
    reply: str
    history: list[ConversationMessage]
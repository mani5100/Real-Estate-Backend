import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from real_estate_backend.ai.schema import ChatRequest, ChatResponse
from real_estate_backend.ai.service import _call_model, _run_agentic_loop
from real_estate_backend.core.config import settings
from real_estate_backend.core.database import get_db
from real_estate_backend.core.logging import logger
from real_estate_backend.auth.dependencies import require_agent
from real_estate_backend.users.model import User

from real_estate_backend.ai.tools import execute_tool
from real_estate_backend.ai.prompts import (
    ConversationMessage
)


router = APIRouter(prefix="/ai", tags=["AI"])

# Maximum tool call iterations per request
# Prevents infinite loops if model keeps calling tools

class ChatRequest(BaseModel):
    message: str | None = None     
    history: list[ConversationMessage] = []
    is_greeting: bool = False


class ChatResponse(BaseModel):
    reply: str
    history: list[ConversationMessage] 
    
    
# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent),
):
    """
    Agent chatbot endpoint.

    On first open (is_greeting=True):
      - Automatically fetches new leads and greets the agent
      - No message needed from the agent

    On subsequent turns:
      - Agent message is appended to history
      - Agentic loop runs until model returns a final text response
      - Updated history is returned so frontend can store it for next turn
    """
    history = request.history

    if request.is_greeting:
        # Inject a system-level trigger so the model knows to greet
        history.append(ConversationMessage(
            role="agent",
            content="GREETING: I just opened the chatbot. Check my new leads and greet me.",
        ))
    else:
        if not request.message:
            return ChatResponse(
                reply="Please send a message.",
                history=history,
            )
        history.append(ConversationMessage(
            role="agent",
            content=request.message,
        ))

    reply, updated_history = await _run_agentic_loop(
        history=history,
        db=db,
        agent_user_id=current_user.id,
    )

    return ChatResponse(
        reply=reply,
        history=updated_history,
    )
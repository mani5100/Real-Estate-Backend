import json
import httpx

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from real_estate_backend.core.config import settings
from real_estate_backend.core.database import get_db
from real_estate_backend.core.logging import logger
from real_estate_backend.auth.dependencies import require_agent
from real_estate_backend.users.model import User

from real_estate_backend.ai.tools import execute_tool
from real_estate_backend.ai.prompts import (
    ConversationMessage,
    ToolCallResponse,
    TextResponse,
    build_prompt,
    parse_model_response,
    parse_ollama_response,
)


router = APIRouter(prefix="/ai", tags=["AI"])

# Maximum tool call iterations per request
# Prevents infinite loops if model keeps calling tools
MAX_ITERATIONS = 5


# ── Request / Response Schemas ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str | None = None      # None on first open (greeting)
    history: list[ConversationMessage] = []
    is_greeting: bool = False       # True on first open — triggers auto tool call


class ChatResponse(BaseModel):
    reply: str
    history: list[ConversationMessage]  # updated history sent back to frontend


# ── Model Caller ─────────────────────────────────────────────────────────────

async def _call_model(prompt: str) -> dict:
    """
    Sends prompt to the custom model endpoint.
    Returns the full response dict — caller decides how to parse it.
    """
    payload = {
        "model": "gpt-oss:latest",
        "prompt": prompt,
        "stream": False,
        "keep_alive": -1,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ai_base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    logger.info("Model response received", extra={
        "has_tool_calls": bool(data.get("tool_calls")),
        "response_preview": str(data.get("response", ""))[:200],
    })

    return data


# ── Agentic Loop ─────────────────────────────────────────────────────────────

async def _run_agentic_loop(
    history: list[ConversationMessage],
    db: Session,
    agent_user_id: int,
) -> tuple[str, list[ConversationMessage]]:
    """
    Core agentic loop — mirrors LangChain/Agents SDK internals:

    1. Build prompt from history
    2. Call model
    3. Parse response
       ├── tool_call → execute tool → append result → loop again
       └── text      → return final reply
    """

    for iteration in range(MAX_ITERATIONS):
        logger.info("Agentic loop iteration", extra={
            "iteration": iteration + 1,
            "history_length": len(history),
        })

        # Step 1 — build prompt from full history
        prompt = build_prompt(history)

        # Step 2 — call model
        data = await _call_model(prompt)
        parsed = parse_ollama_response(data)

        if isinstance(parsed, ToolCallResponse):
            logger.info("Model requested tool", extra={
    "tool": parsed.tool,
    "tool_args": parsed.args,
})

            # Append the assistant's tool call to history
            history.append(ConversationMessage(
                role="assistant",
                content=json.dumps({
                    "type": "tool_call",
                    "tool": parsed.tool,
                    "args": parsed.args,
                }),
            ))

            # Execute the tool against the DB
            tool_result = execute_tool(
                tool_name=parsed.tool,
                args=parsed.args,
                db=db,
                agent_user_id=agent_user_id,
            )

            # Append tool result to history so model sees it next iteration
            history.append(ConversationMessage(
                role="tool_result",
                content=tool_result.model_dump_json(),
            ))

            # Loop — model will now form a response using the tool result
            continue

        if isinstance(parsed, TextResponse):
            # Final answer — append to history and return
            history.append(ConversationMessage(
                role="assistant",
                content=json.dumps({
                    "type": "text",
                    "message": parsed.message,
                }),
            ))

            return parsed.message, history

    # Safety net — if we hit MAX_ITERATIONS without a text response
    fallback = "I was unable to complete the request. Please try again."

    history.append(ConversationMessage(
        role="assistant",
        content=json.dumps({"type": "text", "message": fallback}),
    ))

    return fallback, history


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
import json

from real_estate_backend.ai.schema import ConversationMessage, TextResponse, ToolCallResponse
from real_estate_backend.ai.tools import TOOL_REGISTRY

# Union type used by the parser
AgentResponse = ToolCallResponse | TextResponse
# ── System Prompt Builder ────────────────────────────────────────────────────

def _build_tool_descriptions() -> str:
    """Converts TOOL_REGISTRY into a readable block for the system prompt."""
    lines = []

    for tool in TOOL_REGISTRY:
        lines.append(f"Tool: {tool.name}")
        lines.append(f"Description: {tool.description}")

        if tool.args:
            lines.append("Args:")
            for arg in tool.args:
                required = "required" if arg.required else "optional"
                lines.append(f"  - {arg.name} ({arg.type}, {required}): {arg.description}")
        else:
            lines.append("Args: none")

        lines.append("")  # blank line between tools

    return "\n".join(lines)


SYSTEM_PROMPT = f"""
You are a real estate assistant helping agents manage their leads.
You have access to the following tools:

{_build_tool_descriptions()}

RESPONSE FORMAT RULES — follow these exactly, no exceptions:

1. If you need to call a tool, respond with this JSON and nothing else:
{{
  "type": "tool_call",
  "tool": "<tool_name>",
  "args": {{}}
}}

2. If you have a final answer for the agent, respond with this JSON and nothing else:
{{
  "type": "text",
  "message": "<your response here>"
}}

3. Never mix plain text with JSON. Never add explanations outside the JSON.
4. After receiving a tool result, use it as context to form your next response.
5. Be concise and professional. Address the agent directly.
""".strip()


# ── Prompt Builder ────────────────────────────────────────────────────────────
# Builds the full prompt string sent to the model each turn.
# Format mirrors what LangChain/Agents SDK passes internally.

def build_prompt(history: list[ConversationMessage]) -> str:
    """
    Converts conversation history into a single prompt string.
    The model sees the full history every call — this is its only memory.
    """
    lines = [
        f"[SYSTEM]\n{SYSTEM_PROMPT}",
        "\n[CONVERSATION]",
    ]

    for message in history:
        if message.role == "agent":
            lines.append(f"Agent: {message.content}")
        elif message.role == "assistant":
            lines.append(f"Assistant: {message.content}")
        elif message.role == "tool_result":
            lines.append(f"Tool Result: {message.content}")

    # Signal to the model that it is its turn to respond
    lines.append("Assistant:")

    return "\n".join(lines)


# ── Response Parser ───────────────────────────────────────────────────────────
# Parses raw model text output into a typed Pydantic model.
# If the model returns malformed JSON we return a TextResponse
# with an error message rather than crashing the loop.

def parse_model_response(raw: str) -> AgentResponse:
    """
    Parses raw model output into ToolCallResponse or TextResponse.
    Strips markdown code fences the model might add despite instructions.
    """
    cleaned = raw.strip()

    # Strip markdown fences if model adds them anyway
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        response_type = data.get("type")

        if response_type == "tool_call":
            return ToolCallResponse(
                type="tool_call",
                tool=data["tool"],
                args=data.get("args", {}),
            )

        if response_type == "text":
            return TextResponse(
                type="text",
                message=data["message"],
            )

        return TextResponse(
            type="text",
            message="I encountered an unexpected response format. Please try again.",
        )

    except (json.JSONDecodeError, KeyError):
        return TextResponse(
            type="text",
            message=raw.strip(),
        )
        
        

def parse_ollama_response(data: dict) -> AgentResponse:
    """
    Handles Ollama-style API responses which can come in two shapes:

    Shape 1 — Native tool call (response is empty, tool_calls is populated):
    {
        "response": "",
        "tool_calls": [{"function": {"name": "...", "arguments": {...}}}]
    }

    Shape 2 — Plain text response (response has content, tool_calls absent):
    {
        "response": "You have 3 new leads...",
        "tool_calls": []
    }
    """
    # Shape 1 — native Ollama tool call
    tool_calls = data.get("tool_calls")
    if tool_calls:
        first_call = tool_calls[0]["function"]
        arguments = first_call.get("arguments", {})

        # The model put our full JSON inside arguments
        # Extract tool name and args from it
        tool_name = arguments.get("tool") or first_call.get("name")
        args = arguments.get("args", {})

        return ToolCallResponse(
            type="tool_call",
            tool=tool_name,
            args=args,
        )

    # Shape 2 — plain text response
    response_text = data.get("response", "").strip()
    if response_text:
        return parse_model_response(response_text)

    return TextResponse(
        type="text",
        message="I was unable to generate a response. Please try again.",
    )
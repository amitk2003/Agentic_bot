from typing import List

from app.agent.schemas import UserInput, ToolResult
from app.groq_client import generate_content


async def synthesize_response(
    user_input: UserInput,
    tool_results: List[ToolResult]
) -> str:
    """
    Takes the original query and tool outputs,
    then generates the final user response using Groq.
    """

    results_context = ""

    for idx, res in enumerate(tool_results):
        results_context += (
            f"--- Tool Output {idx + 1}: {res.tool_name} ---\n"
            f"Status: {res.status}\n"
            f"Output:\n{res.result}\n\n"
        )

    # Build conversation history context
    history_context = ""
    if user_input.chat_history:
        history_context = "Previous Conversation:\n"
        for msg in user_input.chat_history[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:1500] if len(msg["content"]) > 1500 else msg["content"]
            history_context += f"{role}: {content}\n\n"

    prompt = f"""
You are a helpful and intelligent AI assistant.

The user's request has already been processed by a set of tools.

{history_context}

Current User Query:
{user_input.query}

Tool Execution Results:
{results_context}

Instructions:

- Answer ONLY using the tool outputs.
- Do not invent information.
- Do not mention internal tools.
- If the user requested bullet points, tables, markdown, or a specific format, preserve it.
- Keep the response clear, concise, and natural.
- Use the conversation history for context if the user refers to previous messages.
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are a helpful AI assistant.",
            temperature=0.3,
        )

    except Exception as e:
        return f"I encountered an error synthesizing the final response: {str(e)}"
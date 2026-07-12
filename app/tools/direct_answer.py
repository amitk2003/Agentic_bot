from . import register_tool
from app.groq_client import generate_content


@register_tool(
    name="direct_answer",
    description="Answers general questions, greetings, or conversation that don't require any specialized tool. Use for hello/hi, general knowledge, or when the answer can be derived from conversation history context.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "The user's question or message to answer directly."
            },
            "context": {
                "type": "STRING",
                "description": "Optional conversation context. Pass relevant info from conversation history if available."
            }
        },
        "required": ["query"]
    }
)
async def direct_answer(query: str, context: str = "") -> str:
    """
    Answers general questions directly using Groq.
    """

    context_section = ""
    if context:
        context_section = f"\nContext:\n{context}\n"

    prompt = f"""
Answer the following user message naturally and helpfully.
{context_section}
User: {query}
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are a helpful AI assistant. Be concise, friendly, and natural.",
            temperature=0.5,
        )

    except Exception as e:
        return f"Error: {str(e)}"

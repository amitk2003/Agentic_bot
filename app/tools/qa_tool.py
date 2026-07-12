from . import register_tool
from app.groq_client import generate_content


@register_tool(
    name="qa_tool",
    description="Answers natural language questions based on the provided text context. Extracts specific information like action items.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "context": {
                "type": "STRING",
                "description": "The text context to search within."
            },
            "question": {
                "type": "STRING",
                "description": "The question to answer based on the context."
            }
        },
        "required": ["context", "question"]
    }
)
async def qa_tool(context: str, question: str) -> str:
    """
    Answers a question using ONLY the provided context.
    """
    # Truncate to ~15000 chars to stay within Groq token limits
    if len(context) > 15000:
        context = context[:15000] + "\n... [context truncated]"

    prompt = f"""
You are an expert question-answering assistant.

Use ONLY the supplied context.

Instructions:

- Answer ONLY from the provided context.
- Never use outside knowledge.
- If the answer is missing, say:
  "I could not find the answer in the provided context."
- Be concise and accurate.
- If the user asks for action items, return only the action items.
- If the user asks for names, dates, or numbers, return only those relevant details.

Question:
{question}

Context:
{context}
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are an expert document question answering assistant.",
            temperature=0.0,
        )

    except Exception as e:
        return f"Error answering question: {str(e)}"
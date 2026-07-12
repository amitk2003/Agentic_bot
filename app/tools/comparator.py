from . import register_tool
from app.groq_client import generate_content


@register_tool(
    name="compare_documents",
    description="Compares the content of two or more texts. Identifies similarities, differences, and answers specific questions about their relation.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "text_a": {
                "type": "STRING",
                "description": "The first text to compare."
            },
            "text_b": {
                "type": "STRING",
                "description": "The second text to compare."
            },
            "query": {
                "type": "STRING",
                "description": "Specific question about how they compare."
            }
        },
        "required": ["text_a", "text_b", "query"]
    }
)
async def compare_documents(text_a: str, text_b: str, query: str) -> str:
    """
    Compare two documents using Groq.
    """

    prompt = f"""
You are an expert document comparison assistant.

Compare the following two texts based ONLY on the user's query.

User Query:
{query}

Text A:
{text_a}

Text B:
{text_b}

Instructions:

- Answer the user's query directly.
- Highlight the major similarities.
- Highlight the major differences.
- If the query asks whether they discuss the same topic,
  clearly answer Yes, Partially, or No.
- If useful, provide a short conclusion.

Return the comparison in clear markdown.
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are an expert document analyst.",
            temperature=0.1,
        )

    except Exception as e:
        return f"Error comparing documents: {str(e)}"
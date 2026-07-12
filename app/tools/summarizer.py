from . import register_tool
from app.groq_client import generate_content


@register_tool(
    name="summarize_text",
    description="Summarizes text into exactly three formats: a 1-line summary, 3 bullet points, and a 5-sentence summary.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "text": {
                "type": "STRING",
                "description": "The text to summarize."
            }
        },
        "required": ["text"]
    }
)
async def summarize_text(text: str) -> str:
    """
    Summarizes text using Groq.
    """
    # Truncate to ~15000 chars to stay within Groq token limits
    if len(text) > 15000:
        text = text[:15000] + "\n... [text truncated for summarization]"

    prompt = f"""
You must summarize the following text.

Your output MUST strictly follow this format.

[1-Line Summary]
(Exactly one line)

[3 Bullet Points]
- Point 1
- Point 2
- Point 3

[5-Sentence Summary]
(Exactly five sentences)

Text:
{text}
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are an expert summarization assistant.",
            temperature=0.2,
        )

    except Exception as e:
        return f"Error summarizing text: {str(e)}"
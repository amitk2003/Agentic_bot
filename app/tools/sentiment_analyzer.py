from . import register_tool
from app.groq_client import generate_content


@register_tool(
    name="analyze_sentiment",
    description="Analyzes the sentiment of the provided text. Returns a label (Positive/Negative/Neutral/Mixed), confidence, and a 1-line justification.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "text": {
                "type": "STRING",
                "description": "The text to analyze."
            }
        },
        "required": ["text"]
    }
)
async def analyze_sentiment(text: str) -> str:
    """
    Analyze sentiment using Groq.
    """

    prompt = f"""
Analyze the sentiment of the following text.

Return STRICTLY in this format:

Label: Positive | Negative | Neutral | Mixed

Confidence: High | Medium | Low

Justification: One short sentence explaining the result.

Text:
{text}
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are an expert sentiment analysis assistant.",
            temperature=0.1,
        )

    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"
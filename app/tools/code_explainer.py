from . import register_tool
from app.groq_client import generate_content


@register_tool(
    name="explain_code",
    description="Explains what a code snippet does, detects potential bugs, and estimates time/space complexity.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "code": {
                "type": "STRING",
                "description": "The code snippet to explain."
            }
        },
        "required": ["code"]
    }
)
async def explain_code(code: str) -> str:
    """
    Explains code using Groq.
    """

    prompt = f"""
You are an expert software engineer.

Analyze the following code and return your answer in this exact format.

## Code Explanation
Explain clearly what the code does.

## Potential Issues
- Mention bugs, edge cases, bad practices or improvements.
- If there are none, explicitly say "No obvious issues detected."

## Time Complexity
State the Big-O time complexity and explain why.

## Space Complexity
State the Big-O space complexity and explain why.

Code:

{code}
"""

    try:
        return generate_content(
            prompt,
            system_prompt="You are an expert software engineer specializing in code reviews and algorithm analysis.",
            temperature=0.1,
        )

    except Exception as e:
        return f"Error explaining code: {str(e)}"
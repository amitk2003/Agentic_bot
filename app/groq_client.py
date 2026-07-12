from openai import OpenAI
from app.config import Config

client = OpenAI(
    api_key=Config.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def generate_content(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.1,
):
    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        raise RuntimeError(f"Groq API Error: {e}")
from google import genai
from app.config import Config

client = genai.Client(
    api_key=Config.GEMINI_API_KEY,
    vertexai=False,
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Reply with Hello"
)

print(response.text)
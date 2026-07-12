import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    GROQ_AUDIO_MODEL = os.getenv(
        "GROQ_AUDIO_MODEL",
        "whisper-large-v3",
    )

    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "models/text-embedding-004",
    )

    UPLOAD_DIR = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "uploads",
    )


os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
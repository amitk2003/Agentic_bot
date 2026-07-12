from app.config import Config
from app.groq_client import client


def extract_audio_transcript(file_path: str) -> str:
    """
    Transcribe audio using Groq Whisper.
    """

    try:
        with open(file_path, "rb") as audio_file:

            transcript = client.audio.transcriptions.create(
                model=Config.GROQ_AUDIO_MODEL,
                file=audio_file,
                response_format="text",
            )

        return transcript.strip()

    except Exception as e:
        return f"[Error transcribing audio: {str(e)}]"
import re

from youtube_transcript_api import YouTubeTranscriptApi

from . import register_tool


@register_tool(
    name="fetch_youtube_transcript",
    description="""
Fetches the transcript of a YouTube video.

Use this tool whenever the user provides a YouTube URL or video ID.

Returns the complete transcript as plain text.
""",
    parameters={
        "type": "OBJECT",
        "properties": {
            "url_or_id": {
                "type": "STRING",
                "description": "YouTube URL or Video ID."
            }
        },
        "required": ["url_or_id"]
    }
)
async def fetch_youtube_transcript(url_or_id: str) -> str:

    youtube_regex = (
        r"(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)"
        r"([A-Za-z0-9_-]{11})"
    )

    match = re.search(youtube_regex, url_or_id)

    if match:
        video_id = match.group(1)
    else:
        video_id = url_or_id.strip()

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        try:
            # Try to fetch English first
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
        except Exception:
            # Fallback to the first available transcript
            transcript = next(iter(transcript_list))
            
        fetched_transcript = transcript.fetch()

        # Build plain text from transcript snippets
        transcript_text = " ".join([snippet.text for snippet in fetched_transcript])

        return transcript_text

    except Exception as e:

        return f"Unable to fetch transcript.\n{str(e)}"
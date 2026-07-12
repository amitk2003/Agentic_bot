import re
import requests
from . import register_tool


@register_tool(
    name="fetch_web_content",
    description="Fetches text content from a given URL (e.g., LinkedIn, articles, websites). Use this whenever the user asks to summarize a link or fetch details from a URL.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "The URL to fetch."
            }
        },
        "required": ["url"]
    }
)
async def fetch_web_content(url: str) -> str:
    """
    Fetches web content using requests and extracts basic text.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        # Adding a small timeout to avoid hanging on unresponsive sites
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # Remove style and script tags to avoid injecting code/css into the summary
        html = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove all other HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Return up to 10k characters to avoid blowing up the LLM context window
        return text[:10000]
        
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

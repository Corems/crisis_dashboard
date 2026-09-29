import os
import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.proxies import GenericProxyConfig

YT_PROXY_URL = os.getenv("YT_PROXY_URL", "")


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)",
        r"youtube\.com\/embed\/([^&\n?#]+)",
        r"youtube\.com\/v\/([^&\n?#]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def get_transcript(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    if not YT_PROXY_URL:
        raise RuntimeError("YT_PROXY_URL is not configured")

    try:
        ytt_api = YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(http_url=YT_PROXY_URL, https_url=YT_PROXY_URL)
        )
        transcript_list = ytt_api.list(video_id)

        try:
            transcript = transcript_list.find_manually_created_transcript(["uk", "ru", "en"])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(["uk", "ru", "en"])

        data = transcript.fetch()
        full_text = " ".join(snippet.text for snippet in data)
        return full_text.strip()

    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video") from None
    except NoTranscriptFound:
        raise ValueError("No transcript available for this video") from None
    except Exception as e:
        raise ValueError(f"Error fetching transcript: {e}") from e

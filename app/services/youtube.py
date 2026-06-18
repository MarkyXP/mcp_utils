import json
import re
import xml.etree.ElementTree as ET

import httpx

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch

ATOM_NS = "http://www.w3.org/2005/Atom"
YOUTUBE_NS = "http://www.youtube.com/xml/schemas/2015"
MEDIA_NS = "http://search.yahoo.com/mrss/"
_CHANNEL_ID_RE = re.compile(r"channel_id=(UC[a-zA-Z0-9_-]*)")
_TRANSCRIBER = YouTubeTranscriptApi()

def _extract_video_id(url_or_id: str) -> str:
    """Extract video ID from a YouTube URL or return it if it's already an ID."""
    if len(url_or_id) == 11:
        return url_or_id
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def search(
    search_term: str,
    num_videos: int = 5,
) -> list[dict]:
    """Search YouTube for videos based on a query.

    Uses langchain_community's YouTubeSearchTool under the hood.

    Args:
        search_term: The search query.
        num_videos: Number of videos to return (default 5, max 50).

    Returns:
        List of dicts with keys: title, url, video_id, channel_name, and duration.
    """
    num_videos = min(max(num_videos, 1), 50)
    results = YoutubeSearch(search_term, max_results=num_videos).to_dict()
    formatted_results = [
        {
            "title": result["title"],
            "url": "http://youtube.com"+result["url_suffix"],
            "video_id": result["id"],
            "channel_name": result["channel"],
            "duration": result["duration"]
        }
        for result in results
    ]
    return formatted_results


def get_transcript(video_url_or_title: str) -> dict:
    """Extract transcript from a YouTube video.

    Args:
        video_url_or_title: YouTube video URL or video ID.

    Returns:
        String with thr transcript
    """
    video_id = _extract_video_id(video_url_or_title)
    transcript = _TRANSCRIBER.fetch(video_id) 
    text = " ".join(
        [
            entry.text
            for entry in transcript.snippets
        ]
    )
    return text


def get_channel_videos(channel_id: str, n: int = 10) -> list[dict]:
    """Fetch the latest n videos from a YouTube channel via its RSS feed.

    Args:
        channel_id: The YouTube channel ID (e.g. UCBJycsmduvYEL83R_U4JriQ).
        n: Number of videos to return (default 10).

    Returns:
        List of dicts with keys: title, video_id, url, published, channel_name, media_description.
    """
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    resp = httpx.get(url, timeout=30.0)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    entries = root.findall(f"{{{ATOM_NS}}}entry")

    videos = []
    for entry in entries[:n]:
        title = entry.findtext(f"{{{ATOM_NS}}}title", "")
        link_el = entry.find(f"{{{ATOM_NS}}}link")
        video_url = link_el.get("href", "") if link_el is not None else ""
        published = entry.findtext(f"{{{ATOM_NS}}}published", "")
        channel_name = entry.findtext(f"{{{ATOM_NS}}}author/{{{ATOM_NS}}}name", "")
        video_id_el = entry.find(f"{{{YOUTUBE_NS}}}videoId")
        video_id = video_id_el.text if video_id_el is not None else ""
        media_description = entry.findtext(
            f"{{{MEDIA_NS}}}group/{{{MEDIA_NS}}}description", ""
        )

        videos.append({
            "title": title,
            "video_id": video_id,
            "url": video_url,
            "published": published,
            "channel_name": channel_name,
            "media_description": media_description,
        })

    return videos


def get_channel_id(channel_name: str) -> str:
    """Resolve a YouTube channel name (handle) to its channel ID.

    Fetches the channel page and extracts the channel ID from the HTML.

    Args:
        channel_name: The channel handle (e.g. ``@MistralAI`` or ``MistralAI``).

    Returns:
        The channel ID string (e.g. ``UCBJycsmduvYEL83R_U4JriQ``).

    Raises:
        ValueError: If the channel ID cannot be found.
    """
    handle = channel_name.strip("\"' @\r\n\t")
    if not handle.startswith("https://"):
        handle = f"https://www.youtube.com/{handle}"
    resp = httpx.get(handle, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()

    match = _CHANNEL_ID_RE.search(resp.text)
    if match:
        return match.group(1)

    raise ValueError(f"Could not find channel ID for: {channel_name}")


if __name__ == "__main__":
    results = search_youtube_videos("python tutorial", num_videos=3)
    print(f"Found {len(results)} videos:")
    for r in results:
        print(f"  - {r['url']}")

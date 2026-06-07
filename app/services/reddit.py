import json
from pathlib import Path

import httpx

_HEADERS_PATH = Path(__file__).resolve().parent.parent.parent / "headers.json"


def _load_headers() -> dict:
    with open(_HEADERS_PATH, "r") as f:
        return json.load(f)


async def get_subreddit(name: str) -> list[dict]:
    """Fetch top daily posts from a subreddit.

    >>> import asyncio
    >>> asyncio.run(get_subreddit("python"))
    [{'title': ..., 'url': ..., 'author': ..., 'score': ..., ...}]
    """
    headers = _load_headers()

    url = f"https://www.reddit.com/r/{name}/top.json?t=day&limit=25"

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        posts.append({
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "author": d.get("author", ""),
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "created_utc": d.get("created_utc", 0),
            "permalink": f"https://www.reddit.com{d.get('permalink', '')}",
        })

    return posts


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=True)

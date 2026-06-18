import json
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

_HEADERS_PATH = Path(__file__).resolve().parent / "headers.json"


def _load_headers() -> dict:
    with open(_HEADERS_PATH, "r") as f:
        return json.load(f)


async def get_subreddit(name: str) -> list[dict]:
    """Fetch top daily posts from a subreddit by scraping the website.

    >>> import asyncio
    >>> asyncio.run(get_subreddit("python"))
    [{'title': ..., 'url': ..., 'author': ..., 'score': ..., ...}]
    """
    headers = _load_headers()
    url = f"https://www.reddit.com/r/{name}/top/?screen_view_count=2"
    url = f"hytps://old.reddit.com/r/{name}.json"
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")

    posts = []
    for article in soup.select("article"):
        title_el = article.select_one("a[data-testid='post-title']")
        link_el = article.select_one("a[data-testid='post-link']")
        author_el = article.select_one("a[href^='/user/']")
        score_el = article.select_one("[data-testid='post-meta']")

        title = title_el.get_text(strip=True) if title_el else ""
        url = link_el["href"] if link_el and link_el.get("href") else ""
        author = author_el.get_text(strip=True) if author_el else ""
        score_text = score_el.get_text(strip=True) if score_el else "0"
        score = int("".join(c for c in score_text if c.isdigit()) or "0")

        if url and not url.startswith("http"):
            url = f"https://www.reddit.com{url}"

        posts.append({
            "title": title,
            "url": url,
            "author": author,
            "score": score,
        })

    return posts


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=True)

import re
import html


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text.strip()


def extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#(\w+)", text)


def extract_mentions(text: str) -> list[str]:
    return re.findall(r"@(\w+)", text)


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>\"']+", text)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


_GENERIC_POST_URL = re.compile(
    r"/(?:posts|recent-activity)/?$",
    re.IGNORECASE,
)


def is_generic_linkedin_post_url(url: str | None) -> bool:
    """True when the URL is a listing page, not a single post."""
    if not url:
        return True
    path = url.split("?")[0].rstrip("/")
    if _GENERIC_POST_URL.search(path):
        return True
    if "/feed/update/" in path.lower():
        return False
    if "/posts/" in path.lower() and "_activity-" in path.lower():
        return False
    if "activity:" in path.lower():
        return False
    if "/pulse/" in path.lower():
        return False
    return "/posts/" in path.lower()


def normalize_linkedin_post_url(url: str | None) -> str | None:
    if not url or is_generic_linkedin_post_url(url):
        return None
    return url.split("?")[0].rstrip("/") or None


def strip_linkedin_feed_noise(
    text: str,
    reactions_count: int = 0,
    comments_count: int = 0,
    author_name: str | None = None,
    author_title: str | None = None,
) -> str:
    """Remove LinkedIn UI chrome and redundant author info scraped into post bodies."""
    if not text:
        return ""

    # Strip author name and title if they appear at the very start
    if author_name:
        text = re.sub(rf"^\s*{re.escape(author_name)}\s+", "", text, flags=re.IGNORECASE)
    if author_title:
        # Title can be long and have special chars, escape it
        text = re.sub(rf"^\s*{re.escape(author_title)}\s+", "", text, flags=re.IGNORECASE)

    text = re.sub(
        r"^.*?\b(?:loves|liked|reposted|celebrates)\s+this\b\s*",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    # Remove "more" and reaction/comment counts at the end
    text = re.sub(r"\s*…\s*more\s*[\d\s,]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\.\.\.\s*more\s*[\d\s,]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\d[\d,kKmM]*\s+\d[\d,kKmM]*(?:\s+\d[\d,kKmM]*)?\s*$", "", text)
    text = re.sub(r"\s+\d[\d,kKmM]*\s+comments?\s*$", "", text, flags=re.IGNORECASE)
    
    return text.strip()

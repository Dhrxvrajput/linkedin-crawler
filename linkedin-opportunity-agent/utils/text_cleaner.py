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

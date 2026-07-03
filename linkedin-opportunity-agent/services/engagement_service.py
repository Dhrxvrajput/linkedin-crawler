import re

from config.settings import get_settings
from llm.groq import get_llm_client
from llm.prompts import GENERATE_CONGRATS_COMMENT_PROMPT
from schemas.post_schema import PostSchema
from utils.helpers import safe_json_loads
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def generate_congrats_comment(post: PostSchema) -> str:
    settings = get_settings()
    fallback = _fallback_comment(post.author.name, settings.comment_max_chars)
    if not settings.groq_api_key:
        return fallback

    try:
        client = get_llm_client()
        prompt = GENERATE_CONGRATS_COMMENT_PROMPT.format(
            author_name=post.author.name,
            author_title=post.author.title or "N/A",
            summary=(post.summary or "")[:600],
            content=post.content[:1200],
            max_chars=settings.comment_max_chars,
        )
        raw = await client.generate_async(prompt)
        parsed = safe_json_loads(raw, default={}) or {}
        comment = _sanitize_comment(parsed.get("comment") or fallback, settings.comment_max_chars)
        return comment or fallback
    except Exception as exc:
        logger.warning("Failed to generate congrats comment for %s: %s", post.id, exc)
        return fallback


def _sanitize_comment(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    text = text.replace("#", "")
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "."
    return text


def _fallback_comment(author_name: str, max_chars: int) -> str:
    first = (author_name or "there").split()[0]
    comment = f"Big congratulations, {first}. Wishing you continued success in this new milestone."
    return _sanitize_comment(comment, max_chars)

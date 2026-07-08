import asyncio

from schemas.post_schema import PostSchema
from llm.factory import get_llm_client
from llm.output_parsers import parse_summary_response
from llm.prompts import SUMMARIZE_PROMPT
from utils.logger import setup_logger

logger = setup_logger(__name__)

MAX_CONCURRENT_SUMMARIES = 5


async def summarize_post(post: PostSchema) -> str:
    """Generate a brief 2-3 sentence summary for a post."""
    if post.summary:
        return post.summary

    try:
        client = get_llm_client()
        prompt = SUMMARIZE_PROMPT.format(
            author_name=post.author.name,
            author_title=post.author.title or "N/A",
            content=post.content[:2000],
        )
        result = await client.generate_json_async(prompt)
        summary_data = parse_summary_response({**result, "post_id": post.id or ""})
        return summary_data.summary or _fallback_summary(post.content)
    except Exception as e:
        logger.warning("Summary failed for %s: %s", post.author.name, e)
        return _fallback_summary(post.content)


async def summarize_posts(posts: list[PostSchema]) -> list[PostSchema]:
    sem = asyncio.Semaphore(MAX_CONCURRENT_SUMMARIES)

    async def _summarize_one(post: PostSchema) -> str | None:
        if post.summary:
            return post.summary
        async with sem:
            try:
                return await summarize_post(post)
            except Exception as e:
                logger.warning("Parallel summary failed for %s: %s", post.author.name, e)
                return _fallback_summary(post.content)

    tasks = [_summarize_one(post) for post in posts]
    summaries = await asyncio.gather(*tasks)

    for post, summary in zip(posts, summaries):
        if summary:
            post.summary = summary

    return posts


def _fallback_summary(content: str) -> str:
    text = content.strip().replace("\n", " ")
    if len(text) <= 200:
        return text
    return text[:197] + "..."

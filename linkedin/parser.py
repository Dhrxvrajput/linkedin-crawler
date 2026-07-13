import re
from datetime import datetime

from schemas.post_schema import PostAuthor, PostSchema
from utils.helpers import generate_post_id, parse_linkedin_date
from utils.text_cleaner import (
    clean_text,
    extract_hashtags,
    extract_urls,
    is_generic_linkedin_post_url,
    normalize_linkedin_post_url,
    strip_linkedin_feed_noise,
)


def parse_post_element(element_data: dict) -> PostSchema | None:
    try:
        reactions_count = _parse_count(element_data.get("reactions_count", "0"))
        comments_count = _parse_count(element_data.get("comments_count", "0"))
        content = clean_text(element_data.get("content", ""))
        content = strip_linkedin_feed_noise(
            content,
            reactions_count=reactions_count,
            comments_count=comments_count,
        )
        if not content or len(content) < 15:
            return None

        author_name = element_data.get("author_name", "Unknown")
        author = PostAuthor(
            name=author_name,
            title=element_data.get("author_title"),
            profile_url=element_data.get("author_profile_url"),
            company=element_data.get("author_company"),
        )

        post_id = generate_post_id(content, author_name)
        posted_time_raw = element_data.get("posted_time")
        posted_at = parse_linkedin_date(posted_time_raw) if posted_time_raw else None

        return PostSchema(
            id=post_id,
            linkedin_post_id=element_data.get("linkedin_post_id"),
            author=author,
            content=content,
            reactions_count=reactions_count,
            comments_count=comments_count,
            post_url=normalize_linkedin_post_url(element_data.get("post_url")),
            image_urls=element_data.get("image_urls", []),
            posted_at=posted_at,
            scraped_at=datetime.utcnow(),
            status="pending",
        )
    except Exception:
        return None


def _parse_count(count_str: str) -> int:
    if not count_str:
        return 0
    count_str = str(count_str).strip().lower().replace(",", "")
    if "k" in count_str:
        return int(float(count_str.replace("k", "")) * 1000)
    if "m" in count_str:
        return int(float(count_str.replace("m", "")) * 1_000_000)
    match = re.search(r"(\d+)", count_str)
    return int(match.group(1)) if match else 0


def enrich_post_metadata(post: PostSchema) -> PostSchema:
    extract_hashtags(post.content)
    post.post_url = normalize_linkedin_post_url(post.post_url)
    if post.post_url:
        return post

    urls = extract_urls(post.content)
    linkedin_urls = [
        normalize_linkedin_post_url(u)
        for u in urls
        if "linkedin.com" in u.lower()
    ]
    linkedin_urls = [u for u in linkedin_urls if u]
    if linkedin_urls:
        post.post_url = linkedin_urls[0]
    elif urls and not is_generic_linkedin_post_url(urls[0]):
        post.post_url = urls[0]
    return post

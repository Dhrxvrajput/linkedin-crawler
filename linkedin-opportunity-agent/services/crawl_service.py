from config.settings import get_settings
from database.crud import upsert_post
from database.db import get_db, setup_database
from linkedin.crawler import fetch_posts
from services.summarize_service import summarize_posts
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def crawl_and_save_feed(max_posts: int | None = None, user_id: int | None = None) -> dict:
    """Fetch latest LinkedIn feed posts, summarize, and save to database."""
    settings = get_settings()
    setup_database()

    browser_profile = None
    session_path = None
    if user_id is not None:
        from services.user_linkedin_service import get_user_linkedin_paths

        browser_profile, session_path = get_user_linkedin_paths(user_id)

    posts = await fetch_posts(max_posts, browser_profile=browser_profile, session_path=session_path)

    if settings.summarize_on_crawl and posts:
        logger.info("Generating brief summaries for %d posts...", len(posts))
        posts = await summarize_posts(posts)

    saved = 0
    with get_db() as db:
        for post in posts:
            upsert_post(db, post)
            saved += 1

    logger.info("Crawl complete: saved %d posts", saved)
    return {
        "posts_fetched": len(posts),
        "posts_saved": saved,
        "sample": [
            {
                "author": p.author.name,
                "posted": str(p.posted_at)[:16] if p.posted_at else "unknown",
                "summary": (p.summary or "")[:80],
            }
            for p in posts[:3]
        ],
    }

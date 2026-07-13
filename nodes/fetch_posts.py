import asyncio

from graph.state import AgentState
from linkedin.crawler import fetch_posts
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def fetch_posts_node(state: AgentState) -> dict:
    max_posts = state.get("max_posts", 50)
    browser_profile = state.get("browser_profile")
    session_path = state.get("session_path")
    
    logger.info("Fetching LinkedIn posts (max=%d)...", max_posts)

    try:
        posts = await fetch_posts(max_posts, browser_profile=browser_profile, session_path=session_path)
        logger.info("Fetched %d posts", len(posts))
        return {
            "posts": posts,
            "current_post_index": 0,
            "processed_count": 0,
        }
    except Exception as e:
        logger.error("Failed to fetch posts: %s", e)
        return {"errors": [f"fetch_posts: {e}"]}

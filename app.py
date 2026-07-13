import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from database.db import setup_database
from graph.builder import compile_graph
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_agent(max_posts: int | None = None) -> dict:
    settings = get_settings()
    setup_database()

    graph = compile_graph()
    initial_state = {
        "posts": [],
        "opportunities": [],
        "people": [],
        "digest": "",
        "errors": [],
        "current_post_index": 0,
        "processed_count": 0,
        "max_posts": max_posts or settings.linkedin_max_posts,
    }

    logger.info("Starting LinkedIn Opportunity Agent (max_posts=%d)", initial_state["max_posts"])
    result = await graph.ainvoke(initial_state)

    opp_count = len(result.get("opportunities", []))
    error_count = len(result.get("errors", []))
    logger.info("Agent complete: %d opportunities, %d errors", opp_count, error_count)

    if result.get("digest"):
        logger.info("Digest generated (%d chars)", len(result["digest"]))

    return result


async def crawl_feed(max_posts: int | None = None, user_id: int | None = None) -> dict:
    """Crawl LinkedIn feed using the LangGraph agent workflow."""
    settings = get_settings()
    setup_database()

    # Get user's LinkedIn session if specified
    browser_profile = None
    session_path = None
    if user_id is not None:
        from services.user_linkedin_service import get_user_linkedin_paths
        browser_profile, session_path = get_user_linkedin_paths(user_id)

    # Run the full LangGraph agent workflow
    graph = compile_graph()
    initial_state = {
        "posts": [],
        "opportunities": [],
        "people": [],
        "digest": "",
        "errors": [],
        "current_post_index": 0,
        "processed_count": 0,
        "max_posts": max_posts or settings.linkedin_max_posts,
        "browser_profile": browser_profile,
        "session_path": session_path,
    }

    logger.info("Starting LinkedIn Agent Workflow (max_posts=%d)", initial_state["max_posts"])
    result = await graph.ainvoke(initial_state)

    # Count saved posts and opportunities
    opp_count = len(result.get("opportunities") or [])
    error_count = len(result.get("errors") or [])
    posts_count = len(result.get("posts") or [])
    
    logger.info("Agent workflow complete: %d posts, %d opportunities, %d errors", 
                posts_count, opp_count, error_count)

    if result.get("digest"):
        logger.info("Digest generated (%d chars)", len(result["digest"]))

    # Prepare sample posts for return value
    sample = []
    posts_list = result.get("posts") or []
    for p in posts_list[:3]:
        try:
            author = "Unknown"
            if hasattr(p, "author") and p.author:
                author = p.author.name
            elif isinstance(p, dict):
                author = p.get("author_name", "Unknown")

            posted = "unknown"
            if hasattr(p, "posted_at") and p.posted_at:
                posted = str(p.posted_at)
            elif isinstance(p, dict):
                posted = str(p.get("posted_at", "unknown"))

            summary = ""
            if hasattr(p, "summary") and p.summary:
                summary = str(p.summary)
            elif isinstance(p, dict):
                summary = str(p.get("summary") or "")

            sample.append({
                "author": author,
                "posted": posted[:16],
                "summary": summary[:80],
            })
        except Exception as e:
            logger.warning("Failed to prepare sample for a post: %s", e)

    # Auto-detect login failure and mark user as disconnected so they can reconnect via dashboard UI
    if user_id is not None and result.get("errors"):
        login_failed = any(
            "login failed" in str(err).lower() or
            "session expired" in str(err).lower() or
            "not logged in" in str(err).lower() or
            "no valid linkedin credentials" in str(err).lower()
            for err in result["errors"]
        )
        if login_failed:
            logger.warning("LinkedIn login failed or session expired for user %d. Resetting connection status.", user_id)
            try:
                from services.auth_service import set_linkedin_disconnected
                set_linkedin_disconnected(user_id)
            except Exception as e:
                logger.error("Failed to set linkedin disconnected in db: %s", e)

    return {
        "posts_fetched": posts_count,
        "posts_saved": posts_count,
        "opportunities_detected": opp_count,
        "errors": error_count,
        "sample": sample,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Opportunity Agent")
    parser.add_argument("--max-posts", type=int, default=None, help="Max posts to fetch")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open browser to log in to LinkedIn (run this once before scraping)",
    )
    parser.add_argument("--user-id", type=int, default=None, help="User ID to operate on")
    parser.add_argument(
        "--debug-feed",
        action="store_true",
        help="Test feed scraping and print diagnostics",
    )
    parser.add_argument(
        "--crawl-only",
        action="store_true",
        help="Crawl LinkedIn feed and save posts (no LLM analysis)",
    )
    args = parser.parse_args()

    if args.crawl_only:
        result = asyncio.run(crawl_feed(max_posts=args.max_posts))
        print(f"\nCrawled {result['posts_fetched']} posts, saved {result['posts_saved']} to database.")
        if result.get("sample"):
            print("Sample:")
            for s in result["sample"]:
                print(
                    f"  {s['author']}: posted {s.get('posted', 'unknown')}, "
                    f"suggested engagement={s.get('engagement', 'ignore')}"
                )
        return

    if args.debug_feed:
        from linkedin.crawler import LinkedInCrawler
        async def _debug():
            async with LinkedInCrawler() as crawler:
                return await crawler.debug_feed()
        result = asyncio.run(_debug())
        print("\nFeed debug results:")
        print(f"  Cards found: {result.get('cards_found', 0)}")
        print(f"  Posts extracted: {len(result.get('posts', []))}")
        print(f"  URL: {result.get('page_url', 'N/A')}")
        if result.get("posts"):
            for p in result["posts"][:5]:
                print(f"\n{p.get('author_name')}: {p.get('reactions_count')} reactions, {p.get('comments_count')} comments")
                print(f"  {p.get('content', '')[:120]}...")
        return

    if args.login:
        from linkedin.crawler import LinkedInCrawler
        
        async def _login(user_id=None):
            browser_profile = None
            session_path = None
            if user_id is not None:
                from services.user_linkedin_service import get_user_linkedin_paths
                browser_profile, session_path = get_user_linkedin_paths(user_id)
            
            async with LinkedInCrawler(
                headless=False,
                browser_profile=browser_profile,
                session_path=session_path
            ) as crawler:
                return await crawler.ensure_logged_in()

        success = asyncio.run(_login(user_id=args.user_id))
        if success:
            if args.user_id:
                from services.user_linkedin_service import set_linkedin_connected
                set_linkedin_connected(args.user_id)
            print("\nLogin successful! Session saved.")
        else:
            print("\nLogin failed. Try again.")
            sys.exit(1)
        return

    if args.dashboard:
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(ROOT / "dashboard" / "streamlit_app.py"),
        ])
        return

    result = asyncio.run(run_agent(max_posts=args.max_posts))

    print(f"\n{'='*50}")
    print(f"LinkedIn Opportunity Agent — Results")
    print(f"{'='*50}")
    print(f"Posts processed: {result.get('processed_count', 0)}")
    print(f"Opportunities found: {len(result.get('opportunities', []))}")
    print(f"People tracked: {len(result.get('people', []))}")

    if result.get("errors"):
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result["errors"]:
            print(f"  - {err}")

    if result.get("digest"):
        print(f"\n{'='*50}")
        print("DIGEST")
        print(f"{'='*50}")
        print(result["digest"])


if __name__ == "__main__":
    main()

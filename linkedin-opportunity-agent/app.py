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
    from services.crawl_service import crawl_and_save_feed
    return await crawl_and_save_feed(max_posts, user_id=user_id)


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
        from linkedin.crawler import interactive_login
        success = asyncio.run(interactive_login())
        if success:
            print("\nLogin successful! Session saved. You can now run: python app.py")
        else:
            print("\nLogin failed. Try again with: python app.py --login")
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

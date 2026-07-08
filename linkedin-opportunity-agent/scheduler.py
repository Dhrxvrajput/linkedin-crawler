import asyncio
import time
from datetime import datetime, timedelta

from app import crawl_feed
from database.crud import get_all_connected_users
from database.db import get_db, setup_database
from utils.logger import setup_logger

logger = setup_logger("scheduler")

async def update_all_users():
    """Loops through all users and updates their LinkedIn feed."""
    logger.info("--- Starting Universal Update Loop ---")
    setup_database()
    
    with get_db() as db:
        users = get_all_connected_users(db)
        logger.info(f"Found {len(users)} users with connected LinkedIn sessions.")
        
        for user in users:
            logger.info(f"Updating feed for User: {user.email} (ID: {user.id})")
            try:
                # We reuse the crawl_feed logic from app.py
                # This runs the full AI agent workflow for THIS specific user
                result = await crawl_feed(user_id=user.id)
                logger.info(f"Success for {user.email}: {result['posts_fetched']} posts, {result['opportunities_detected']} opportunities.")
            except Exception as e:
                logger.error(f"Failed to update {user.email}: {str(e)}")
            
            # Small pause between users to avoid local resource spikes
            await asyncio.sleep(5)

    logger.info("--- Universal Update Loop Complete ---")

async def main():
    while True:
        try:
            await update_all_users()
        except Exception as e:
            logger.error(f"Critical scheduler error: {e}")
        
        # Log wait time
        next_run = datetime.now() + timedelta(hours=12)
        logger.info(f"Sleeping for 12 hours. Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Wait for 12 hours before next update
        await asyncio.sleep(12 * 3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")

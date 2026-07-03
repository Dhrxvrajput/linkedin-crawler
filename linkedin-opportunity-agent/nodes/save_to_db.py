from graph.state import AgentState
from database.crud import upsert_opportunity, upsert_person, upsert_post
from database.db import get_db
from utils.logger import setup_logger

logger = setup_logger(__name__)


def save_to_db_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    opportunities = state.get("opportunities", [])
    people = state.get("people", [])

    logger.info(
        "Saving to database: %d posts, %d opportunities, %d people",
        len(posts), len(opportunities), len(people),
    )

    try:
        with get_db() as db:
            for post in posts:
                upsert_post(db, post)

            for opp in opportunities:
                upsert_opportunity(db, opp)

            for person in people:
                upsert_person(db, person)

        logger.info("Database save complete")
        return {}
    except Exception as e:
        logger.error("Database save failed: %s", e)
        return {"errors": [f"save_to_db: {e}"]}

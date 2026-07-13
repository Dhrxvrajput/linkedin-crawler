import hashlib
from graph.state import AgentState
from database.crud import upsert_opportunity, upsert_person, upsert_post, upsert_post_cache
from database.db import get_db
from nodes.check_cache import get_stable_post_id
from utils.logger import setup_logger

logger = setup_logger(__name__)


def save_to_db_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    opportunities = state.get("opportunities", [])
    people = state.get("people", [])
    cache_miss_ids = state.get("cache_miss_ids", [])

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

            # Upsert Post Cache for any posts that had a cache miss or were newly analyzed
            for post in posts:
                if post.id in cache_miss_ids:
                    # Find corresponding person details
                    person_data = None
                    for p in people:
                        if p.profile_url == post.author.profile_url:
                            person_data = {
                                "name": p.name,
                                "title": p.title,
                                "company": p.company,
                                "profile_url": p.profile_url,
                                "relationship_type": p.relationship_type,
                                "relevance_score": p.relevance_score,
                                "mutual_connections": p.mutual_connections,
                                "shared_interests": p.shared_interests,
                                "recent_activity": p.recent_activity,
                                "notes": p.notes
                            }
                            break

                    # Find opportunities details
                    opps_data = []
                    for opp in opportunities:
                        if opp.post_id == post.id:
                            opps_data.append({
                                "title": opp.title,
                                "description": opp.description,
                                "opportunity_type": opp.opportunity_type,
                                "domain": opp.domain,
                                "relevance_score": opp.relevance_score,
                                "confidence_score": opp.confidence_score,
                                "author_name": opp.author_name,
                                "author_profile_url": opp.author_profile_url,
                                "relationship_type": opp.relationship_type,
                                "action_items": opp.action_items,
                                "tags": opp.tags,
                                "status": opp.status
                            })

                    cache_key = get_stable_post_id(post)
                    content_hash = hashlib.sha256(post.content.encode('utf-8')).hexdigest()
                    cache_data = {
                        "post_id": cache_key,
                        "content_hash": content_hash,
                        "author_name": post.author.name,
                        "post_url": post.post_url,
                        "summary": post.summary,
                        "classification": post.domain,
                        "sentiment": getattr(post, 'sentiment', None),
                        "suggested_reply": post.engagement_comment,
                        "relationship_analysis": person_data,
                        "opportunity_data": opps_data
                    }
                    upsert_post_cache(db, cache_data)
                    logger.debug(">>> Cache POPULATED/UPDATED for post %s.", cache_key)

        logger.debug("Database save complete")
        return {}
    except Exception as e:
        logger.error("Database save failed: %s", e)
        return {"errors": [f"save_to_db: {e}"]}

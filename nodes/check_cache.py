import hashlib
import re
from datetime import datetime
from graph.state import AgentState
from database.db import get_db
from database.crud import get_post_cache
from schemas.opportunity_schema import OpportunitySchema
from schemas.people_schema import PersonSchema
from utils.logger import setup_logger

logger = setup_logger(__name__)


def get_stable_post_id(post) -> str:
    # 1. Use real LinkedIn post ID on the object if present and not mock
    if post.linkedin_post_id and not post.linkedin_post_id.startswith("post-"):
        return post.linkedin_post_id
    
    # 2. Extract URN activity ID from URL if possible
    if post.post_url:
        # e.g. urn:li:activity:7123456789
        urn_match = re.search(r'(urn:li:(?:activity|share|ugcPost|comment):\d+)', post.post_url)
        if urn_match:
            return urn_match.group(1)
        # e.g. status/activity/7123456789
        num_match = re.search(r'(?:activity|update|posts)/(\d+)', post.post_url)
        if num_match:
            return f"urn:li:activity:{num_match.group(1)}"
        num_match_dash = re.search(r'_activity-(\d+)', post.post_url)
        if num_match_dash:
            return f"urn:li:activity:{num_match_dash.group(1)}"
    
    # 3. Fallback to deterministic SHA-256 hash from stable attributes
    posted_str = post.posted_at.isoformat() if post.posted_at else ""
    raw_key = f"{post.post_url or ''}|{post.author.name}|{post.content}|{posted_str}"
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


async def check_cache_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)
    cache_miss_ids = list(state.get("cache_miss_ids", []))
    opportunities = list(state.get("opportunities", []))
    people = list(state.get("people", []))

    if index >= len(posts):
        return {}

    post = posts[index]
    
    # Generate Cache Key and Content Hash
    cache_key = get_stable_post_id(post)
    content_hash = hashlib.sha256(post.content.encode('utf-8')).hexdigest()
    
    logger.debug("Checking cache for post %d/%d by %s (Key: %s)", index + 1, len(posts), post.author.name, cache_key)
    
    try:
        with get_db() as db:
            record = get_post_cache(db, cache_key)
            
            if record and record.content_hash == content_hash:
                logger.debug(">>> Cache HIT for post %s. Content unchanged. Skipping LLM nodes.", cache_key)
                
                # Fetch cached analysis results
                post.summary = record.summary
                post.domain = record.classification
                post.sentiment = record.sentiment
                post.engagement_comment = record.suggested_reply
                posts[index] = post
                
                # Load opportunities if cached
                if record.opportunity_data:
                    for opp_dict in record.opportunity_data:
                        opp = OpportunitySchema(**opp_dict)
                        # Ensure correct post_id linking
                        opp.post_id = post.id
                        if not any(o.post_id == post.id and o.title == opp.title for o in opportunities):
                            opportunities.append(opp)
                            logger.debug("Loaded cached Opportunity: '%s'", opp.title)
                            
                # Load relationship analysis if cached
                if record.relationship_analysis:
                    person = PersonSchema(**record.relationship_analysis)
                    if not any(p.profile_url == person.profile_url for p in people):
                        people.append(person)
                        logger.debug("Loaded cached Person: '%s'", person.name)
                        
                return {
                    "posts": posts,
                    "opportunities": opportunities,
                    "people": people,
                    "cache_hit": True
                }
            
            elif record:
                logger.debug(">>> Cache HIT but content changed (Content Hash: %s vs cached %s). Re-running LLM nodes.", content_hash, record.content_hash)
            else:
                logger.debug(">>> Cache MISS for post %s. Running LLM nodes.", cache_key)
                
            cache_miss_ids.append(post.id)
            return {
                "cache_hit": False,
                "cache_miss_ids": cache_miss_ids
            }
            
    except Exception as e:
        logger.error("Error in check_cache_node for post %s: %s", post.id, e)
        # Fallback to normal execution on cache error
        cache_miss_ids.append(post.id)
        return {
            "cache_hit": False,
            "cache_miss_ids": cache_miss_ids,
            "errors": [f"check_cache:{post.id}: {e}"]
        }

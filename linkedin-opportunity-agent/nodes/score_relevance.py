from graph.state import AgentState
from llm.groq import get_llm_client
from llm.output_parsers import parse_relevance_response
from llm.prompts import SCORE_RELEVANCE_PROMPT
from schemas.user_schema import UserProfile
from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def score_relevance_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)
    opportunities = list(state.get("opportunities", []))

    if index >= len(posts):
        return {}

    post = posts[index]
    settings = get_settings()
    user = UserProfile.from_settings(settings)

    post_opps = [o for o in opportunities if o.post_id == post.id]
    if not post_opps:
        return {"current_post_index": index + 1, "processed_count": state.get("processed_count", 0) + 1}

    logger.info("Scoring relevance for %d opportunities from %s", len(post_opps), post.author.name)

    try:
        client = get_llm_client()
        updated_opps = []

        for opp in opportunities:
            if opp.post_id != post.id:
                updated_opps.append(opp)
                continue

            prompt = SCORE_RELEVANCE_PROMPT.format(
                user_name=user.name or "User",
                user_title=user.title or "N/A",
                user_company=user.company or "N/A",
                user_interests=", ".join(user.interests) or "N/A",
                user_skills=", ".join(user.skills) or "N/A",
                title=opp.title,
                opportunity_type=opp.opportunity_type,
                description=opp.description,
                domain=opp.domain or "other",
                author_name=opp.author_name or "Unknown",
                relationship_type=opp.relationship_type or "unknown",
            )
            result = await client.generate_json_async(prompt)
            relevance = parse_relevance_response(result)
            opp.relevance_score = relevance["relevance_score"]
            if relevance.get("recommended_actions"):
                opp.action_items = list(set(opp.action_items + relevance["recommended_actions"]))
            updated_opps.append(opp)
            logger.info("Scored '%s': %.2f", opp.title, opp.relevance_score)

        return {
            "opportunities": updated_opps,
            "current_post_index": index + 1,
            "processed_count": state.get("processed_count", 0) + 1,
        }
    except Exception as e:
        logger.error("Relevance scoring failed: %s", e)
        return {
            "errors": [f"score_relevance:{post.id}: {e}"],
            "current_post_index": index + 1,
            "processed_count": state.get("processed_count", 0) + 1,
        }

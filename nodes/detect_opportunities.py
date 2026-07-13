from graph.state import AgentState
from llm.factory import get_llm_client
from llm.output_parsers import parse_opportunity_response
from llm.prompts import DETECT_OPPORTUNITY_PROMPT
from schemas.opportunity_schema import OpportunitySchema
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def detect_opportunities_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)
    opportunities = list(state.get("opportunities", []))

    if index >= len(posts):
        return {}

    if state.get("cache_hit"):
        return {"opportunities": opportunities}

    post = posts[index]
    logger.info("Detecting opportunities in post by %s", post.author.name)

    try:
        client = get_llm_client()
        prompt = DETECT_OPPORTUNITY_PROMPT.format(
            author_name=post.author.name,
            summary=post.summary or "",
            domain=post.domain or "other",
            content=post.content[:1500],
        )
        result = await client.generate_json_async(prompt)
        detection = parse_opportunity_response(result)

        if detection.is_opportunity:
            opp = OpportunitySchema(
                post_id=post.id,
                title=detection.title or "Untitled Opportunity",
                description=detection.description or "",
                opportunity_type=detection.opportunity_type or "other",
                domain=post.domain,
                confidence_score=detection.confidence_score,
                author_name=post.author.name,
                author_profile_url=post.author.profile_url,
                action_items=detection.action_items,
                tags=detection.tags,
            )
            opportunities.append(opp)
            logger.info("Opportunity detected: %s", opp.title)

        return {"opportunities": opportunities}
    except Exception as e:
        logger.error("Opportunity detection failed: %s", e)
        return {"errors": [f"detect_opportunities:{post.id}: {e}"]}

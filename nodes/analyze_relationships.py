from graph.state import AgentState
from llm.factory import get_llm_client
from llm.output_parsers import parse_relationship_response
from llm.prompts import ANALYZE_RELATIONSHIP_PROMPT
from schemas.people_schema import PersonSchema
from schemas.user_schema import UserProfile
from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def analyze_relationships_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)
    people = list(state.get("people", []))
    opportunities = list(state.get("opportunities", []))

    if index >= len(posts):
        return {}

    if state.get("cache_hit"):
        return {
            "people": people,
            "opportunities": opportunities,
        }

    post = posts[index]
    settings = get_settings()
    user = UserProfile.from_settings(settings)

    logger.info("Analyzing relationship with %s", post.author.name)

    try:
        client = get_llm_client()
        prompt = ANALYZE_RELATIONSHIP_PROMPT.format(
            user_name=user.name or "User",
            user_title=user.title or "N/A",
            user_company=user.company or "N/A",
            user_interests=", ".join(user.interests) or "N/A",
            user_skills=", ".join(user.skills) or "N/A",
            author_name=post.author.name,
            author_title=post.author.title or "N/A",
            author_company=post.author.company or "N/A",
            summary=post.summary or post.content[:500],
        )
        result = await client.generate_json_async(prompt)
        analysis = parse_relationship_response({**result, "person_name": post.author.name})

        person = PersonSchema(
            name=post.author.name,
            title=post.author.title,
            company=post.author.company,
            profile_url=post.author.profile_url,
            relationship_type=analysis.relationship_type,
            relevance_score=analysis.relevance_score,
            mutual_connections=analysis.mutual_connections,
            shared_interests=analysis.shared_interests,
            recent_activity=post.summary,
        )
        people.append(person)

        for opp in opportunities:
            if opp.post_id == post.id:
                opp.relationship_type = analysis.relationship_type

        return {
            "people": people,
            "opportunities": opportunities,
        }
    except Exception as e:
        logger.error("Relationship analysis failed: %s", e)
        return {"errors": [f"analyze_relationships:{post.id}: {e}"]}

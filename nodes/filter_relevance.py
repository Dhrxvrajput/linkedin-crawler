from graph.state import AgentState
from llm.factory import get_llm_client
from llm.output_parsers import parse_post_relevance_response
from llm.prompts import POST_RELEVANCE_FILTER_PROMPT
from schemas.user_schema import UserProfile
from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def filter_relevance_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)

    if index >= len(posts):
        return {}

    post = posts[index]

    # If it is a cache hit, check cached classification
    if state.get("cache_hit"):
        is_relevant = (post.domain != "irrelevant")
        logger.debug("Relevance Filtering (Cache HIT): post by %s is %s", 
                    post.author.name, "RELEVANT" if is_relevant else "IRRELEVANT")
        return {"is_relevant": is_relevant}

    # For cache miss, retrieve profile relevance via LLM
    settings = get_settings()
    user = UserProfile.from_settings(settings)

    logger.info("Evaluating relevance of post by %s against user profile", post.author.name)

    try:
        client = get_llm_client()
        prompt = POST_RELEVANCE_FILTER_PROMPT.format(
            user_name=user.name or "User",
            user_title=user.title or "N/A",
            user_company=user.company or "N/A",
            user_interests=", ".join(user.interests) or "N/A",
            user_skills=", ".join(user.skills) or "N/A",
            author_name=post.author.name,
            author_title=post.author.title or "N/A",
            content=post.content[:2000]
        )

        result = await client.generate_json_async(prompt)
        parsed = parse_post_relevance_response(result)
        is_relevant = parsed.get("is_relevant", True)

        if not is_relevant:
            logger.info("Post by %s marked IRRELEVANT. Skipping deep analysis. Reasoning: %s", 
                        post.author.name, parsed.get("reasoning", "No reasoning provided"))
            post.domain = "irrelevant"
            post.summary = "Post skipped: Not relevant to profile."
            posts[index] = post

            return {
                "posts": posts,
                "is_relevant": False
            }

        logger.info("Post by %s marked RELEVANT. Continuing analysis.", post.author.name)
        return {
            "is_relevant": True
        }
    except Exception as e:
        logger.error("Relevance filtering failed: %s", e)
        # Fallback to True under errors to avoid dropping valid opportunities
        return {
            "is_relevant": True
        }

from graph.state import AgentState
from llm.factory import get_llm_client
from llm.output_parsers import parse_domain_response
from llm.prompts import CLASSIFY_DOMAIN_PROMPT
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def classify_domain_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)

    if index >= len(posts):
        return {}

    post = posts[index]
    logger.info("Classifying domain for post by %s", post.author.name)

    try:
        client = get_llm_client()
        prompt = CLASSIFY_DOMAIN_PROMPT.format(
            summary=post.summary or "",
            content=post.content[:1500],
        )
        result = await client.generate_json_async(prompt)
        domain_data = parse_domain_response(result)
        post.domain = domain_data["domain"]
        posts[index] = post

        return {"posts": posts}
    except Exception as e:
        logger.error("Domain classification failed: %s", e)
        return {"errors": [f"classify_domain:{post.id}: {e}"]}

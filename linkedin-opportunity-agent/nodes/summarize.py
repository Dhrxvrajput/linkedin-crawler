from graph.state import AgentState
from llm.groq import get_llm_client
from llm.output_parsers import parse_summary_response
from llm.prompts import SUMMARIZE_PROMPT
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def summarize_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    index = state.get("current_post_index", 0)

    if index >= len(posts):
        return {}

    post = posts[index]
    logger.info("Summarizing post %d/%d by %s", index + 1, len(posts), post.author.name)

    try:
        client = get_llm_client()
        prompt = SUMMARIZE_PROMPT.format(
            author_name=post.author.name,
            author_title=post.author.title or "N/A",
            content=post.content[:2000],
        )
        result = await client.generate_json_async(prompt)
        summary_data = parse_summary_response({**result, "post_id": post.id})
        post.summary = summary_data.summary
        posts[index] = post

        return {
            "posts": posts,
            "current_post_index": index,
        }
    except Exception as e:
        logger.error("Summarize failed for post %s: %s", post.id, e)
        return {"errors": [f"summarize:{post.id}: {e}"]}

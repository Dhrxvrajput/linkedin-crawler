import asyncio
from graph.state import AgentState
from llm.factory import get_llm_client
from llm.output_parsers import parse_summary_response
from llm.prompts import SUMMARIZE_PROMPT
from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def process_single_post(post, client, user_profile):
    """Summarize a single post (no domain/opportunity/relationship analysis)."""
    try:
        # Summarize only
        summary_prompt = SUMMARIZE_PROMPT.format(
            author_name=post.author.name,
            author_title=post.author.title or "N/A",
            content=post.content[:2000],
        )
        summary_result = await client.generate_json_async(summary_prompt)
        summary_data = parse_summary_response({**summary_result, "post_id": post.id})
        post.summary = summary_data.summary

        return {
            "post": post,
            "person": None,
            "opportunities": [],
            "error": None
        }
    except Exception as e:
        logger.error("Failed to process post by %s: %s", post.author.name, e)
        return {"error": str(e), "post": post}

async def process_posts_batch_node(state: AgentState) -> dict:
    posts = state.get("posts", [])
    if not posts:
        return {}

    settings = get_settings()
    from schemas.user_schema import UserProfile
    user_profile = UserProfile.from_settings(settings)
    client = get_llm_client()
    
    logger.info("Summarizing %d posts in parallel...", len(posts))
    
    sem = asyncio.Semaphore(5)
    
    async def sem_process(p):
        async with sem:
            res = await process_single_post(p, client, user_profile)
            await asyncio.sleep(0.1)
            return res

    tasks = [sem_process(p) for p in posts]
    results = await asyncio.gather(*tasks)
    
    processed_posts = []
    all_people = []
    all_opportunities = []
    errors = []
    
    for res in results:
        if res.get("error"):
            errors.append(f"Post processing error: {res['error']}")
            processed_posts.append(res["post"])
            continue
            
        processed_posts.append(res["post"])
        if res.get("person"):
            all_people.append(res["person"])
        if res.get("opportunities"):
            all_opportunities.extend(res["opportunities"])
            
    return {
        "posts": processed_posts,
        "people": all_people,
        "opportunities": all_opportunities,
        "errors": errors,
        "processed_count": len(processed_posts)
    }


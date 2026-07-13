from graph.state import AgentState
from llm.factory import get_llm_client
from llm.prompts import GENERATE_DIGEST_PROMPT
from config.settings import get_settings
from database.crud import create_digest
from database.db import get_db
from utils.helpers import ensure_dir
from utils.logger import setup_logger
from datetime import datetime
from pathlib import Path

logger = setup_logger(__name__)


async def generate_digest_node(state: AgentState) -> dict:
    opportunities = state.get("opportunities", [])
    settings = get_settings()

    if not opportunities:
        return {"digest": "No opportunities found in this run."}

    sorted_opps = sorted(opportunities, key=lambda o: o.relevance_score, reverse=True)
    top_opps = sorted_opps[: settings.digest_top_n]

    opportunities_text = "\n\n".join(
        f"**{i+1}. {opp.title}** (Score: {opp.relevance_score:.2f})\n"
        f"Type: {opp.opportunity_type} | Domain: {opp.domain}\n"
        f"Author: {opp.author_name}\n"
        f"{opp.description}\n"
        f"Actions: {', '.join(opp.action_items)}"
        for i, opp in enumerate(top_opps)
    )

    logger.info("Generating digest for %d opportunities", len(top_opps))

    try:
        client = get_llm_client()
        prompt = GENERATE_DIGEST_PROMPT.format(
            user_name=settings.user_name or "User",
            user_title=settings.user_title or "Professional",
            user_company=settings.user_company or "N/A",
            opportunities_text=opportunities_text,
        )
        digest = await client.generate_async(prompt)

        with get_db() as db:
            create_digest(db, digest, len(top_opps))

        export_dir = ensure_dir(settings.export_dir)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        digest_path = Path(export_dir) / f"digest_{timestamp}.md"
        digest_path.write_text(digest)
        logger.debug("Digest saved to %s", digest_path)

        return {"digest": digest}
    except Exception as e:
        logger.error("Digest generation failed: %s", e)
        return {"errors": [f"generate_digest: {e}"], "digest": ""}

from graph.state import AgentState
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def skip_post_node(state: AgentState) -> dict:
    index = state.get("current_post_index", 0)
    logger.debug("Skipping post index %d to proceed to next", index)
    return {
        "current_post_index": index + 1,
        "processed_count": state.get("processed_count", 0) + 1
    }

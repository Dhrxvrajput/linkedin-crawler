from graph.state import AgentState


def should_continue_processing(state: AgentState) -> str:
    if state.get("current_post_index", 0) < len(state.get("posts", [])):
        return "process_post"
    return "save_to_db"


def has_opportunities(state: AgentState) -> str:
    if state.get("opportunities"):
        return "generate_digest"
    return "end"


def route_after_fetch(state: AgentState) -> str:
    if state.get("posts"):
        return "summarize"
    return "end"

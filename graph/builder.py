from langgraph.graph import END, StateGraph

from config.constants import (
    NODE_ANALYZE_RELATIONSHIPS,
    NODE_CLASSIFY_DOMAIN,
    NODE_DETECT_OPPORTUNITIES,
    NODE_FETCH_POSTS,
    NODE_GENERATE_DIGEST,
    NODE_SAVE_TO_DB,
    NODE_SCORE_RELEVANCE,
    NODE_SUMMARIZE,
    NODE_CHECK_CACHE,
    NODE_FILTER_RELEVANCE,
    NODE_SKIP_POST,
)
from graph.routing import (
    has_opportunities,
    route_after_fetch,
    should_continue_processing,
    route_after_relevance,
)
from graph.state import AgentState
from nodes.fetch_posts import fetch_posts_node
from nodes.check_cache import check_cache_node
from nodes.filter_relevance import filter_relevance_node
from nodes.summarize import summarize_node
from nodes.classify_domain import classify_domain_node
from nodes.score_relevance import score_relevance_node
from nodes.detect_opportunities import detect_opportunities_node
from nodes.analyze_relationships import analyze_relationships_node
from nodes.skip_post import skip_post_node
from nodes.save_to_db import save_to_db_node
from nodes.generate_digest import generate_digest_node

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node(NODE_FETCH_POSTS, fetch_posts_node)
    graph.add_node(NODE_CHECK_CACHE, check_cache_node)
    graph.add_node(NODE_FILTER_RELEVANCE, filter_relevance_node)
    graph.add_node(NODE_SUMMARIZE, summarize_node)
    graph.add_node(NODE_CLASSIFY_DOMAIN, classify_domain_node)
    graph.add_node(NODE_DETECT_OPPORTUNITIES, detect_opportunities_node)
    graph.add_node(NODE_ANALYZE_RELATIONSHIPS, analyze_relationships_node)
    graph.add_node(NODE_SCORE_RELEVANCE, score_relevance_node)
    graph.add_node(NODE_SKIP_POST, skip_post_node)
    graph.add_node(NODE_SAVE_TO_DB, save_to_db_node)
    graph.add_node(NODE_GENERATE_DIGEST, generate_digest_node)

    graph.set_entry_point(NODE_FETCH_POSTS)

    graph.add_conditional_edges(NODE_FETCH_POSTS, route_after_fetch, {
        "check_cache": NODE_CHECK_CACHE,
        "end": END,
    })

    graph.add_edge(NODE_CHECK_CACHE, NODE_FILTER_RELEVANCE)

    graph.add_conditional_edges(NODE_FILTER_RELEVANCE, route_after_relevance, {
        "summarize": NODE_SUMMARIZE,
        "skip": NODE_SKIP_POST,
    })

    graph.add_edge(NODE_SUMMARIZE, NODE_CLASSIFY_DOMAIN)
    graph.add_edge(NODE_CLASSIFY_DOMAIN, NODE_DETECT_OPPORTUNITIES)
    graph.add_edge(NODE_DETECT_OPPORTUNITIES, NODE_ANALYZE_RELATIONSHIPS)
    graph.add_edge(NODE_ANALYZE_RELATIONSHIPS, NODE_SCORE_RELEVANCE)
    
    graph.add_conditional_edges(NODE_SCORE_RELEVANCE, should_continue_processing, {
        "check_cache": NODE_CHECK_CACHE,
        "save_to_db": NODE_SAVE_TO_DB,
    })

    graph.add_conditional_edges(NODE_SKIP_POST, should_continue_processing, {
        "check_cache": NODE_CHECK_CACHE,
        "save_to_db": NODE_SAVE_TO_DB,
    })

    graph.add_conditional_edges(NODE_SAVE_TO_DB, has_opportunities, {
        NODE_GENERATE_DIGEST: NODE_GENERATE_DIGEST,
        "end": END,
    })

    graph.add_edge(NODE_GENERATE_DIGEST, END)

    return graph


def compile_graph():
    return build_graph().compile()

from typing import Annotated, TypedDict

from schemas.opportunity_schema import OpportunitySchema
from schemas.people_schema import PersonSchema
from schemas.post_schema import PostSchema


def merge_errors(left: list, right: list) -> list:
    return left + right


class AgentState(TypedDict):
    posts: list[PostSchema]
    opportunities: list[OpportunitySchema]
    people: list[PersonSchema]
    digest: str
    errors: Annotated[list[str], merge_errors]
    current_post_index: int
    processed_count: int
    max_posts: int
    browser_profile: str | None
    session_path: str | None
    cache_hit: bool
    cache_miss_ids: list[str]
    is_relevant: bool

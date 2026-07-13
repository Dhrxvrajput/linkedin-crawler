from typing import Any

from pydantic import BaseModel, Field, ValidationError

from schemas.opportunity_schema import OpportunityDetection
from schemas.people_schema import RelationshipAnalysis
from schemas.post_schema import PostSummary


def parse_summary_response(data: dict[str, Any]) -> PostSummary:
    return PostSummary(
        post_id=data.get("post_id", ""),
        summary=data.get("summary", ""),
        key_topics=data.get("key_topics", []),
        sentiment=data.get("sentiment"),
    )


def parse_domain_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": data.get("domain", "other"),
        "confidence": float(data.get("confidence", 0.5)),
        "reasoning": data.get("reasoning", ""),
    }


def parse_opportunity_response(data: Any) -> OpportunityDetection:
    # Recursively unwrap lists to find the dictionary
    while isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    if not isinstance(data, dict):
        return OpportunityDetection(is_opportunity=False)
    try:
        return OpportunityDetection(**data)
    except ValidationError:
        return OpportunityDetection(is_opportunity=False)


def parse_relationship_response(data: dict[str, Any]) -> RelationshipAnalysis:
    try:
        return RelationshipAnalysis(
            person_name=data.get("person_name", ""),
            relationship_type=data.get("relationship_type", "unknown"),
            relevance_score=float(data.get("relevance_score", 0.0)),
            mutual_connections=int(data.get("mutual_connections", 0)),
            shared_interests=data.get("shared_interests", []),
            reasoning=data.get("reasoning"),
        )
    except (ValidationError, TypeError, ValueError):
        return RelationshipAnalysis(
            person_name="",
            relationship_type="unknown",
            relevance_score=0.0,
        )


def parse_relevance_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "relevance_score": float(data.get("relevance_score", 0.0)),
        "reasoning": data.get("reasoning", ""),
        "recommended_actions": data.get("recommended_actions", []),
    }


def parse_post_relevance_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "is_relevant": bool(data.get("is_relevant", True)),
        "confidence": float(data.get("confidence", 0.5)),
        "reasoning": data.get("reasoning", ""),
    }

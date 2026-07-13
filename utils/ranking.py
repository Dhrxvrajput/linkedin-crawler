from typing import Any


def score_opportunity(
    relevance: float,
    confidence: float,
    relationship_boost: float = 0.0,
    recency_boost: float = 0.0,
) -> float:
    base = (relevance * 0.5) + (confidence * 0.3)
    return min(1.0, base + relationship_boost + recency_boost)


def rank_items(items: list[dict[str, Any]], score_key: str = "relevance_score") -> list[dict[str, Any]]:
    return sorted(items, key=lambda x: x.get(score_key, 0), reverse=True)


def filter_by_threshold(
    items: list[dict[str, Any]],
    score_key: str,
    threshold: float,
) -> list[dict[str, Any]]:
    return [item for item in items if item.get(score_key, 0) >= threshold]

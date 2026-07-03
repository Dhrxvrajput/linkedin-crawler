from database.crud import get_opportunities, update_opportunity_status
from database.db import get_db
from schemas.opportunity_schema import OpportunitySchema


class OpportunityService:
    def __init__(self, min_score: float = 0.0):
        self.min_score = min_score

    def get_all(self, limit: int = 50, status: str | None = None) -> list[OpportunitySchema]:
        with get_db() as db:
            opps = get_opportunities(db, limit=limit, status=status, min_score=self.min_score)
            # Deduplicate by opportunity id — keep most recently detected
            seen: dict[int, OpportunitySchema] = {}
            for o in opps:
                schema = self._to_schema(o)
                key = schema.id or id(o)
                prev = seen.get(key)
                if not prev or (schema.detected_at or 0) >= (prev.detected_at or 0):
                    seen[key] = schema
            return list(seen.values())

    def get_top(self, n: int = 10) -> list[OpportunitySchema]:
        opps = self.get_all(limit=500)
        from services.relevance_service import RelevanceService
        ranker = RelevanceService()
        return ranker.rank(opps)[:n]

    def update_status(self, opp_id: int, status: str) -> bool:
        with get_db() as db:
            result = update_opportunity_status(db, opp_id, status)
            return result is not None

    def filter_by_type(self, opportunity_type: str) -> list[OpportunitySchema]:
        return [o for o in self.get_all(limit=200) if o.opportunity_type == opportunity_type]

    @staticmethod
    def _to_schema(opp) -> OpportunitySchema:
        return OpportunitySchema(
            id=opp.id,
            post_id=opp.post_id,
            title=opp.title,
            description=opp.description,
            opportunity_type=opp.opportunity_type,
            domain=opp.domain,
            relevance_score=opp.relevance_score,
            confidence_score=opp.confidence_score,
            author_name=opp.author_name,
            author_profile_url=opp.author_profile_url,
            relationship_type=opp.relationship_type,
            action_items=opp.action_items or [],
            tags=opp.tags or [],
            status=opp.status,
            detected_at=opp.detected_at,
        )

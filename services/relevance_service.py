from config.settings import get_settings
from schemas.opportunity_schema import OpportunitySchema
from schemas.user_schema import UserProfile
from utils.ranking import filter_by_threshold, score_opportunity


class RelevanceService:
    def __init__(self):
        self.settings = get_settings()
        self.user = UserProfile.from_settings(self.settings)

    def score(self, opportunity: OpportunitySchema) -> float:
        relationship_boost = 0.1 if opportunity.relationship_type == "direct_connection" else 0.0
        return score_opportunity(
            relevance=opportunity.relevance_score,
            confidence=opportunity.confidence_score,
            relationship_boost=relationship_boost,
        )

    def filter_relevant(self, opportunities: list[OpportunitySchema]) -> list[OpportunitySchema]:
        threshold = self.settings.relevance_score_threshold
        return [
            o for o in opportunities
            if o.relevance_score >= threshold
        ]

    def rank(self, opportunities: list[OpportunitySchema]) -> list[OpportunitySchema]:
        return sorted(opportunities, key=lambda o: self.score(o), reverse=True)

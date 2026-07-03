from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OpportunitySchema(BaseModel):
    id: Optional[int] = None
    post_id: Optional[str] = None
    title: str
    description: str
    opportunity_type: str
    domain: Optional[str] = None
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    author_name: Optional[str] = None
    author_profile_url: Optional[str] = None
    relationship_type: Optional[str] = None
    action_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: str = "new"
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class OpportunityDetection(BaseModel):
    is_opportunity: bool
    opportunity_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    confidence_score: float = 0.0
    action_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PersonSchema(BaseModel):
    id: Optional[int] = None
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    profile_url: Optional[str] = None
    relationship_type: str = "unknown"
    relevance_score: float = 0.0
    mutual_connections: int = 0
    shared_interests: list[str] = Field(default_factory=list)
    recent_activity: Optional[str] = None
    last_seen: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class RelationshipAnalysis(BaseModel):
    person_name: str
    relationship_type: str
    relevance_score: float = 0.0
    mutual_connections: int = 0
    shared_interests: list[str] = Field(default_factory=list)
    reasoning: Optional[str] = None

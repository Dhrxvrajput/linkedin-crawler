from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PostAuthor(BaseModel):
    name: str
    title: Optional[str] = None
    profile_url: Optional[str] = None
    company: Optional[str] = None


class PostSchema(BaseModel):
    id: Optional[str] = None
    linkedin_post_id: Optional[str] = None
    author: PostAuthor
    content: str
    summary: Optional[str] = None
    domain: Optional[str] = None
    sentiment: Optional[str] = None
    reactions_count: int = 0
    comments_count: int = 0
    post_url: Optional[str] = None
    image_urls: list[str] = Field(default_factory=list)
    posted_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
    engagement_decision: str = "ignore"
    engagement_reason: Optional[str] = None
    engagement_comment: Optional[str] = None
    engagement_status: str = "pending"
    engagement_error: Optional[str] = None
    engagement_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostSummary(BaseModel):
    post_id: str
    summary: str
    key_topics: list[str] = Field(default_factory=list)
    sentiment: Optional[str] = None

from typing import Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    name: str = ""
    title: str = ""
    company: str = ""
    interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    target_domains: list[str] = Field(default_factory=list)
    target_opportunity_types: list[str] = Field(default_factory=list)
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None

    @classmethod
    def from_settings(cls, settings) -> "UserProfile":
        return cls(
            name=settings.user_name,
            title=settings.user_title,
            company=settings.user_company,
            interests=[i.strip() for i in settings.user_interests.split(",") if i.strip()],
            skills=[s.strip() for s in settings.user_skills.split(",") if s.strip()],
        )

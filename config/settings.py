from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


def _strip(v: str) -> str:
    return v.strip() if isinstance(v, str) else v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "LinkedIn Opportunity Agent"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'storage' / 'opportunities.db'}"

    # LinkedIn
    linkedin_email: str = ""
    linkedin_password: str = ""
    linkedin_session_path: str = str(BASE_DIR / "storage" / "sessions" / "linkedin.json")
    linkedin_browser_profile: str = str(BASE_DIR / "storage" / "browser_profile")
    linkedin_headless: bool = True
    linkedin_max_posts: int = 100
    auth_required: bool = True
    linkedin_scroll_pause: float = 2.0
    summarize_on_crawl: bool = True
    auto_like_enabled: bool = False
    auto_comment_enabled: bool = False
    engagement_dry_run: bool = True
    max_engagements_per_run: int = 3
    comment_max_chars: int = 110

    # LLM Settings
    llm_provider: str = "google" # "groq" or "google"
    
    # Groq LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    groq_temperature: float = 0.3
    groq_max_tokens: int = 4096

    # Google LLM (Gemini)
    google_api_key: str = ""
    google_model: str = "gemini-3.5-flash"
    google_temperature: float = 0.3

    # User profile (for relevance scoring)
    user_name: str = ""
    user_title: str = ""
    user_company: str = ""
    user_interests: str = ""
    user_skills: str = ""

    # Scoring thresholds
    opportunity_score_threshold: float = 0.6
    relevance_score_threshold: float = 0.5

    # Digest
    digest_top_n: int = 10
    export_dir: str = str(BASE_DIR / "storage" / "exports")

    @field_validator(
        "linkedin_email", "linkedin_password", "groq_api_key", "google_api_key",
        "user_name", "user_title", "user_company", "user_interests", "user_skills",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, v):
        return _strip(v) if v is not None else v


@lru_cache
def get_settings() -> Settings:
    return Settings()

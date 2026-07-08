from datetime import datetime
from functools import lru_cache
from typing import Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import get_settings


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    linkedin_post_id = Column(String, nullable=True)
    author_name = Column(String, nullable=False)
    author_title = Column(String, nullable=True)
    author_profile_url = Column(String, nullable=True)
    author_company = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    domain = Column(String, nullable=True)
    reactions_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    post_url = Column(String, nullable=True)
    image_urls = Column(JSON, default=list)
    posted_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    engagement_decision = Column(String, default="ignore")
    engagement_reason = Column(Text, nullable=True)
    engagement_comment = Column(Text, nullable=True)
    engagement_status = Column(String, default="pending")
    engagement_error = Column(Text, nullable=True)
    engagement_updated_at = Column(DateTime, nullable=True)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    opportunity_type = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    relevance_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    author_name = Column(String, nullable=True)
    author_profile_url = Column(String, nullable=True)
    relationship_type = Column(String, nullable=True)
    action_items = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    status = Column(String, default="new")
    detected_at = Column(DateTime, default=datetime.utcnow)


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    profile_url = Column(String, nullable=True, unique=True)
    relationship_type = Column(String, default="unknown")
    relevance_score = Column(Float, default=0.0)
    mutual_connections = Column(Integer, default=0)
    shared_interests = Column(JSON, default=list)
    recent_activity = Column(Text, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class Digest(Base):
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    opportunity_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow)


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    linkedin_connected = Column(Integer, default=0)
    linkedin_connected_at = Column(DateTime, nullable=True)
    linkedin_browser_profile = Column(String, nullable=True)
    linkedin_session_path = Column(String, nullable=True)
    user_title = Column(String, nullable=True)
    user_company = Column(String, nullable=True)
    user_interests = Column(Text, nullable=True)
    user_skills = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine)


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_post_columns(engine)
    _ensure_app_user_columns(engine)


def _ensure_post_columns(engine):
    """Best-effort schema evolution for existing SQLite databases."""
    required_columns = {
        "engagement_decision": "TEXT DEFAULT 'ignore'",
        "engagement_reason": "TEXT",
        "engagement_comment": "TEXT",
        "engagement_status": "TEXT DEFAULT 'pending'",
        "engagement_error": "TEXT",
        "engagement_updated_at": "DATETIME",
    }
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(posts)")).fetchall()
        existing = {r[1] for r in rows}
        for col, ddl in required_columns.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE posts ADD COLUMN {col} {ddl}"))


def _ensure_app_user_columns(engine):
    """Best-effort schema evolution for app_users table."""
    required_columns = {
        "linkedin_connected": "INTEGER DEFAULT 0",
        "linkedin_connected_at": "DATETIME",
        "linkedin_browser_profile": "TEXT",
        "linkedin_session_path": "TEXT",
        "user_title": "TEXT",
        "user_company": "TEXT",
        "user_interests": "TEXT",
        "user_skills": "TEXT",
    }
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(app_users)")).fetchall()
        if not rows:
            return
        existing = {r[1] for r in rows}
        for col, ddl in required_columns.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE app_users ADD COLUMN {col} {ddl}"))

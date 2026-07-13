from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import AppUser, Digest, Opportunity, Person, Post, PostCache
from schemas.opportunity_schema import OpportunitySchema
from schemas.people_schema import PersonSchema
from schemas.post_schema import PostSchema


def create_post(db: Session, post: PostSchema) -> Post:
    db_post = Post(
        id=post.id,
        linkedin_post_id=post.linkedin_post_id,
        author_name=post.author.name,
        author_title=post.author.title,
        author_profile_url=post.author.profile_url,
        author_company=post.author.company,
        content=post.content,
        summary=post.summary,
        domain=post.domain,
        reactions_count=post.reactions_count,
        comments_count=post.comments_count,
        post_url=post.post_url,
        image_urls=post.image_urls,
        posted_at=post.posted_at,
        scraped_at=post.scraped_at,
        status=post.status,
        engagement_decision=post.engagement_decision,
        engagement_reason=post.engagement_reason,
        engagement_comment=post.engagement_comment,
        engagement_status=post.engagement_status,
        engagement_error=post.engagement_error,
        engagement_updated_at=post.engagement_updated_at,
    )
    db.add(db_post)
    db.flush()
    return db_post


def get_post(db: Session, post_id: str) -> Optional[Post]:
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts(db: Session, limit: int | None = None, status: Optional[str] = None, exclude_irrelevant: bool = True) -> list[Post]:
    query = db.query(Post)
    if exclude_irrelevant:
        query = query.filter((Post.domain != "irrelevant") | (Post.domain.is_(None)))
    if status:
        query = query.filter(Post.status == status)
    query = query.order_by(func.coalesce(Post.posted_at, Post.scraped_at).desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def count_posts(db: Session, exclude_irrelevant: bool = True) -> int:
    query = db.query(Post)
    if exclude_irrelevant:
        query = query.filter((Post.domain != "irrelevant") | (Post.domain.is_(None)))
    return query.count()


def get_posts_for_engagement(
    db: Session,
    limit: int = 20,
    decision: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Post]:
    query = db.query(Post)
    if decision:
        query = query.filter(Post.engagement_decision == decision)
    if status:
        query = query.filter(Post.engagement_status == status)
    return (
        query.order_by(func.coalesce(Post.posted_at, Post.scraped_at).desc())
        .limit(limit)
        .all()
    )


def update_post(db: Session, post_id: str, **kwargs) -> Optional[Post]:
    post = get_post(db, post_id)
    if post:
        for key, value in kwargs.items():
            setattr(post, key, value)
        db.flush()
    return post


def update_post_engagement(
    db: Session,
    post_id: str,
    engagement_status: str,
    error: Optional[str] = None,
) -> Optional[Post]:
    post = get_post(db, post_id)
    if not post:
        return None
    post.engagement_status = engagement_status
    post.engagement_error = error
    post.engagement_updated_at = datetime.utcnow()
    db.flush()
    return post


def upsert_post(db: Session, post: PostSchema) -> Post:
    existing = get_post(db, post.id)
    if existing:
        existing.linkedin_post_id = post.linkedin_post_id
        existing.author_name = post.author.name
        existing.author_title = post.author.title
        existing.author_profile_url = post.author.profile_url
        existing.author_company = post.author.company
        existing.content = post.content
        if post.summary:
            existing.summary = post.summary
        existing.domain = post.domain
        existing.reactions_count = post.reactions_count
        existing.comments_count = post.comments_count
        existing.post_url = post.post_url or existing.post_url
        existing.image_urls = post.image_urls
        existing.posted_at = post.posted_at
        existing.scraped_at = post.scraped_at or datetime.utcnow()
        existing.status = "processed"
        existing.engagement_decision = post.engagement_decision
        existing.engagement_reason = post.engagement_reason
        existing.engagement_comment = post.engagement_comment
        existing.engagement_status = post.engagement_status
        existing.engagement_error = post.engagement_error
        existing.engagement_updated_at = post.engagement_updated_at
        db.flush()
        return existing
    return create_post(db, post)


def upsert_opportunity(db: Session, opp: OpportunitySchema) -> Opportunity:
    existing = None
    if opp.post_id:
        existing = (
            db.query(Opportunity)
            .filter(Opportunity.post_id == opp.post_id)
            .order_by(Opportunity.detected_at.desc())
            .first()
        )

    if existing:
        existing.title = opp.title
        existing.description = opp.description
        existing.opportunity_type = opp.opportunity_type
        existing.domain = opp.domain
        existing.relevance_score = opp.relevance_score
        existing.confidence_score = opp.confidence_score
        existing.author_name = opp.author_name
        existing.author_profile_url = opp.author_profile_url
        existing.relationship_type = opp.relationship_type
        existing.action_items = opp.action_items
        existing.tags = opp.tags
        existing.detected_at = opp.detected_at or datetime.utcnow()
        db.flush()
        return existing
    return create_opportunity(db, opp)


def create_opportunity(db: Session, opp: OpportunitySchema) -> Opportunity:
    db_opp = Opportunity(
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
        action_items=opp.action_items,
        tags=opp.tags,
        status=opp.status,
        detected_at=opp.detected_at,
    )
    db.add(db_opp)
    db.flush()
    return db_opp


def get_opportunities(
    db: Session,
    limit: int = 50,
    status: Optional[str] = None,
    min_score: float = 0.0,
) -> list[Opportunity]:
    query = db.query(Opportunity).filter(Opportunity.relevance_score >= min_score)
    if status:
        query = query.filter(Opportunity.status == status)
    return query.order_by(Opportunity.detected_at.desc()).limit(limit).all()


def update_opportunity_status(db: Session, opp_id: int, status: str) -> Optional[Opportunity]:
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if opp:
        opp.status = status
        db.flush()
    return opp


def upsert_person(db: Session, person: PersonSchema) -> Person:
    existing = None
    if person.profile_url:
        existing = db.query(Person).filter(Person.profile_url == person.profile_url).first()

    if existing:
        existing.name = person.name
        existing.title = person.title
        existing.company = person.company
        existing.relationship_type = person.relationship_type
        existing.relevance_score = person.relevance_score
        existing.mutual_connections = person.mutual_connections
        existing.shared_interests = person.shared_interests
        existing.recent_activity = person.recent_activity
        existing.last_seen = person.last_seen or datetime.utcnow()
        db.flush()
        return existing

    db_person = Person(
        name=person.name,
        title=person.title,
        company=person.company,
        profile_url=person.profile_url,
        relationship_type=person.relationship_type,
        relevance_score=person.relevance_score,
        mutual_connections=person.mutual_connections,
        shared_interests=person.shared_interests,
        recent_activity=person.recent_activity,
        last_seen=person.last_seen or datetime.utcnow(),
        notes=person.notes,
    )
    db.add(db_person)
    db.flush()
    return db_person


def get_people(db: Session, limit: int = 50, min_score: float = 0.0) -> list[Person]:
    return (
        db.query(Person)
        .filter(Person.relevance_score >= min_score)
        .order_by(Person.relevance_score.desc())
        .limit(limit)
        .all()
    )


def create_digest(db: Session, content: str, opportunity_count: int) -> Digest:
    digest = Digest(content=content, opportunity_count=opportunity_count)
    db.add(digest)
    db.flush()
    return digest


def get_latest_digest(db: Session) -> Optional[Digest]:
    return db.query(Digest).order_by(Digest.generated_at.desc()).first()


def get_user_by_email(db: Session, email: str) -> Optional[AppUser]:
    return db.query(AppUser).filter(AppUser.email == email.strip().lower()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[AppUser]:
    return db.query(AppUser).filter(AppUser.id == user_id).first()


def get_all_connected_users(db: Session) -> list[AppUser]:
    """Returns all users who have successfully connected LinkedIn."""
    return db.query(AppUser).filter(AppUser.linkedin_connected == 1).all()


def create_app_user(db: Session, email: str, password_hash: str, name: str | None = None) -> AppUser:
    user = AppUser(
        email=email.strip().lower(),
        password_hash=password_hash,
        name=name,
        linkedin_connected=0,
    )
    db.add(user)
    db.flush()
    from utils.user_paths import linkedin_profile_dir, linkedin_session_file

    profile = linkedin_profile_dir(user.id)
    profile.mkdir(parents=True, exist_ok=True)
    user.linkedin_browser_profile = str(profile)
    user.linkedin_session_path = str(linkedin_session_file(user.id))
    db.flush()
    return user


def mark_linkedin_connected(db: Session, user_id: int) -> Optional[AppUser]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.linkedin_connected = 1
    user.linkedin_connected_at = datetime.utcnow()
    db.flush()
    return user


def get_post_cache(db: Session, post_id: str) -> Optional[PostCache]:
    return db.query(PostCache).filter(PostCache.post_id == post_id).first()


def upsert_post_cache(db: Session, cache_data: dict) -> PostCache:
    post_id = cache_data["post_id"]
    existing = get_post_cache(db, post_id)
    if existing:
        for k, v in cache_data.items():
            setattr(existing, k, v)
        existing.processed_at = datetime.utcnow()
        db.flush()
        return existing

    db_cache = PostCache(**cache_data)
    db.add(db_cache)
    db.flush()
    return db_cache

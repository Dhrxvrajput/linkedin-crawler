import pytest
from datetime import datetime

from database.db import setup_database, get_db
from database.crud import create_post, create_opportunity, get_posts, get_opportunities, upsert_person
from schemas.post_schema import PostAuthor, PostSchema
from schemas.opportunity_schema import OpportunitySchema
from schemas.people_schema import PersonSchema


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    from config.settings import get_settings
    get_settings.cache_clear()
    setup_database()
    yield
    get_settings.cache_clear()


class TestDatabase:
    def test_create_and_get_post(self):
        post = PostSchema(
            id="test-post-1",
            author=PostAuthor(name="Alice", title="Engineer"),
            content="We are hiring senior engineers for our AI team.",
            domain="technology",
        )
        with get_db() as db:
            create_post(db, post)
            posts = get_posts(db)
            assert len(posts) == 1
            assert posts[0].author_name == "Alice"

    def test_create_opportunity(self):
        opp = OpportunitySchema(
            post_id="test-post-1",
            title="Senior Engineer Role",
            description="AI team hiring",
            opportunity_type="hiring",
            relevance_score=0.85,
            confidence_score=0.9,
            author_name="Alice",
        )
        with get_db() as db:
            create_opportunity(db, opp)
            opps = get_opportunities(db)
            assert len(opps) == 1
            assert opps[0].title == "Senior Engineer Role"

    def test_upsert_person(self):
        person = PersonSchema(
            name="Bob",
            title="CTO",
            company="TechCorp",
            relationship_type="industry_peer",
            relevance_score=0.75,
        )
        with get_db() as db:
            upsert_person(db, person)
            from database.crud import get_people
            people = get_people(db)
            assert len(people) == 1
            assert people[0].name == "Bob"

    def test_filter_opportunities_by_score(self):
        with get_db() as db:
            for i, score in enumerate([0.9, 0.3, 0.7]):
                create_opportunity(db, OpportunitySchema(
                    post_id=f"p{i}",
                    title=f"Opp {i}",
                    description="test",
                    opportunity_type="job",
                    relevance_score=score,
                ))
            high_score = get_opportunities(db, min_score=0.6)
            assert len(high_score) == 2

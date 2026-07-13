import pytest
import hashlib
from datetime import datetime

from database.db import setup_database, get_db
from database.crud import get_post_cache, upsert_post_cache
from schemas.post_schema import PostSchema, PostAuthor
from schemas.opportunity_schema import OpportunitySchema
from schemas.people_schema import PersonSchema
from nodes.check_cache import get_stable_post_id, check_cache_node
from nodes.save_to_db import save_to_db_node


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    from config.settings import get_settings
    from database.models import get_engine
    get_settings.cache_clear()
    get_engine.cache_clear()
    setup_database()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()


class TestCaching:
    def test_get_stable_post_id(self):
        post = PostSchema(
            id="test-1",
            linkedin_post_id="post-12345",  # Starts with post-, so it's a mock/fallback test
            author=PostAuthor(name="John Doe", title="Manager"),
            content="This is post content",
            post_url="https://linkedin.com/feed/update/urn:li:activity:7890123"
        )
        # Should extract urn:li:activity:7890123
        stable_id = get_stable_post_id(post)
        assert stable_id == "urn:li:activity:7890123"

        post_fallback = PostSchema(
            id="test-2",
            linkedin_post_id="post-abc",
            author=PostAuthor(name="Jane Doe", title="CEO"),
            content="Some text content here",
            post_url=None
        )
        # Should generate a hash fallback
        stable_id_fallback = get_stable_post_id(post_fallback)
        assert len(stable_id_fallback) == 64

    def test_cache_crud(self):
        with get_db() as db:
            cache_data = {
                "post_id": "test-cache-id",
                "content_hash": "hash123",
                "author_name": "Jane",
                "post_url": "url1",
                "summary": "This is a cached summary.",
                "classification": "technology",
                "sentiment": "neutral",
                "suggested_reply": "Suggest reply",
                "relationship_analysis": {"name": "Jane", "relationship_type": "industry_peer"},
                "opportunity_data": [{"title": "Job Opp"}]
            }
            upsert_post_cache(db, cache_data)

            cached_item = get_post_cache(db, "test-cache-id")
            assert cached_item is not None
            assert cached_item.summary == "This is a cached summary."
            assert cached_item.classification == "technology"
            assert cached_item.opportunity_data == [{"title": "Job Opp"}]
            assert cached_item.relationship_analysis == {"name": "Jane", "relationship_type": "industry_peer"}

    @pytest.mark.anyio
    async def test_cache_hit_and_miss_pipeline_flow(self):
        # 1. Setup initial post
        post = PostSchema(
            id="p1",
            author=PostAuthor(name="Alice", title="CTO", profile_url="https://linkedin.com/in/alice"),
            content="We are looking for interns.",
            posted_at=datetime.utcnow()
        )

        state = {
            "posts": [post],
            "current_post_index": 0,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        # 2. Run check cache - Expect Cache Miss
        res = await check_cache_node(state)
        assert res["cache_hit"] is False
        assert "p1" in res["cache_miss_ids"]

        # 3. Simulate pipeline execution (summarizing and detecting opportunities)
        post.summary = "Summarized intern request."
        post.domain = "technology"
        post.sentiment = "positive"
        post.engagement_comment = "Great opportunity! I have shared this."

        opp = OpportunitySchema(
            post_id="p1",
            title="Intern Search",
            description="Alice is looking for interns",
            opportunity_type="hiring",
            domain="technology",
            relevance_score=0.8
        )

        person = PersonSchema(
            name="Alice",
            title="CTO",
            profile_url="https://linkedin.com/in/alice",
            relationship_type="industry_peer",
            relevance_score=0.7
        )

        state = {
            "posts": [post],
            "current_post_index": 0,
            "cache_miss_ids": ["p1"],
            "opportunities": [opp],
            "people": [person]
        }

        # 4. Save to DB (this should populate the cache)
        save_to_db_node(state)

        # Confirm database contains cache row
        cache_key = get_stable_post_id(post)
        with get_db() as db:
            record = get_post_cache(db, cache_key)
            assert record is not None
            assert record.summary == "Summarized intern request."
            assert record.opportunity_data[0]["title"] == "Intern Search"

        # 5. Run next execution loop - New state with clean post (no summary or parsed data)
        fresh_post = PostSchema(
            id="p1",
            author=PostAuthor(name="Alice", title="CTO", profile_url="https://linkedin.com/in/alice"),
            content="We are looking for interns.",  # Same content
            posted_at=post.posted_at
        )

        next_state = {
            "posts": [fresh_post],
            "current_post_index": 0,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        # 6. Run check cache - Expect Cache HIT
        hit_res = await check_cache_node(next_state)
        assert hit_res["cache_hit"] is True
        
        # Verify cached values populated on post schema object
        cached_post = hit_res["posts"][0]
        assert cached_post.summary == "Summarized intern request."
        assert cached_post.domain == "technology"
        assert cached_post.sentiment == "positive"
        assert cached_post.engagement_comment == "Great opportunity! I have shared this."

        # Verify cached entities loaded into arrays
        assert len(hit_res["opportunities"]) == 1
        assert hit_res["opportunities"][0].title == "Intern Search"
        assert len(hit_res["people"]) == 1
        assert hit_res["people"][0].name == "Alice"

        # 7. Test cache miss when content changes
        modified_post = PostSchema(
            id="p1",
            author=PostAuthor(name="Alice", title="CTO", profile_url="https://linkedin.com/in/alice"),
            content="We are looking for SENIOR engineers.",  # Changed content!
            posted_at=post.posted_at
        )

        mod_state = {
            "posts": [modified_post],
            "current_post_index": 0,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        mod_res = await check_cache_node(mod_state)
        assert mod_res["cache_hit"] is False
        assert "p1" in mod_res["cache_miss_ids"]

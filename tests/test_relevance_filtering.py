import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from database.db import setup_database, get_db
from database.crud import upsert_post_cache
from schemas.post_schema import PostSchema, PostAuthor
from graph.state import AgentState
from nodes.filter_relevance import filter_relevance_node
from nodes.skip_post import skip_post_node


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


class TestRelevanceFiltering:
    @pytest.mark.anyio
    @patch("nodes.filter_relevance.get_llm_client")
    async def test_relevance_miss_relevant(self, mock_get_client):
        # Mock LLM response saying it's relevant
        mock_client = MagicMock()
        mock_client.generate_json_async = AsyncMock(return_value={"is_relevant": True, "confidence": 0.9})
        mock_get_client.return_value = mock_client

        post = PostSchema(
            id="p_rel",
            author=PostAuthor(name="John Doe", title="Engineer"),
            content="Hiring Senior Python Engineer with LangGraph experience.",
            posted_at=datetime.utcnow()
        )

        state = {
            "posts": [post],
            "current_post_index": 0,
            "cache_hit": False,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        res = await filter_relevance_node(state)
        assert res["is_relevant"] is True
        mock_client.generate_json_async.assert_called_once()

    @pytest.mark.anyio
    @patch("nodes.filter_relevance.get_llm_client")
    async def test_relevance_miss_irrelevant(self, mock_get_client):
        # Mock LLM response saying it's irrelevant
        mock_client = MagicMock()
        mock_client.generate_json_async = AsyncMock(
            return_value={"is_relevant": False, "confidence": 0.95, "reasoning": "Unrelated family milestone update"}
        )
        mock_get_client.return_value = mock_client

        post = PostSchema(
            id="p_irrel",
            author=PostAuthor(name="Jane Doe", title="Accountant"),
            content="I am happy to announce my daughter graduated today!",
            posted_at=datetime.utcnow()
        )

        state = {
            "posts": [post],
            "current_post_index": 0,
            "cache_hit": False,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        res = await filter_relevance_node(state)
        assert res["is_relevant"] is False
        assert res["posts"][0].domain == "irrelevant"
        assert "skipped" in res["posts"][0].summary.lower()
        mock_client.generate_json_async.assert_called_once()

    @pytest.mark.anyio
    @patch("nodes.filter_relevance.get_llm_client")
    async def test_relevance_cache_hit_relevant(self, mock_get_client):
        # Mock LLM client - should NOT be called on cache hit
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        post = PostSchema(
            id="p_cache_rel",
            author=PostAuthor(name="Alice", title="Manager"),
            content="Some tech talk content here",
            posted_at=datetime.utcnow(),
            domain="technology"  # Not irrelevant
        )

        state = {
            "posts": [post],
            "current_post_index": 0,
            "cache_hit": True,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        res = await filter_relevance_node(state)
        assert res["is_relevant"] is True
        mock_client.generate_json_async.assert_not_called()

    @pytest.mark.anyio
    @patch("nodes.filter_relevance.get_llm_client")
    async def test_relevance_cache_hit_irrelevant(self, mock_get_client):
        # Mock LLM client - should NOT be called on cache hit
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        post = PostSchema(
            id="p_cache_irrel",
            author=PostAuthor(name="Bob", title="Dentist"),
            content="A dentist update",
            posted_at=datetime.utcnow(),
            domain="irrelevant"  # Irrelevant
        )

        state = {
            "posts": [post],
            "current_post_index": 0,
            "cache_hit": True,
            "cache_miss_ids": [],
            "opportunities": [],
            "people": []
        }

        res = await filter_relevance_node(state)
        assert res["is_relevant"] is False
        mock_client.generate_json_async.assert_not_called()

    @pytest.mark.anyio
    async def test_skip_post_node(self):
        state = {
            "current_post_index": 2,
            "processed_count": 5
        }
        res = await skip_post_node(state)
        assert res["current_post_index"] == 3
        assert res["processed_count"] == 6

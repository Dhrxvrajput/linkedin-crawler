import pytest
from linkedin.parser import parse_post_element, _parse_count, enrich_post_metadata
from schemas.post_schema import PostAuthor, PostSchema


class TestParser:
    def test_parse_post_element_valid(self):
        raw = {
            "content": "We are hiring a senior engineer to join our AI team. Apply now!",
            "author_name": "Jane Doe",
            "author_title": "CTO at TechCorp",
            "reactions_count": "1.2k",
            "comments_count": "45",
            "posted_time": "2h",
        }
        post = parse_post_element(raw)
        assert post is not None
        assert post.author.name == "Jane Doe"
        assert post.reactions_count == 1200
        assert post.comments_count == 45

    def test_parse_post_element_too_short(self):
        raw = {"content": "Hi", "author_name": "Test"}
        assert parse_post_element(raw) is None

    def test_parse_count(self):
        assert _parse_count("1.2k") == 1200
        assert _parse_count("3.5m") == 3_500_000
        assert _parse_count("42") == 42
        assert _parse_count("") == 0

    def test_enrich_post_metadata(self):
        post = PostSchema(
            id="test1",
            author=PostAuthor(name="Test"),
            content="Check out https://example.com #AI #hiring",
        )
        enriched = enrich_post_metadata(post)
        assert enriched.post_url == "https://example.com"

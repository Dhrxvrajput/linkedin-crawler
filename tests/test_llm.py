import pytest
from unittest.mock import MagicMock, patch

from llm.output_parsers import (
    parse_domain_response,
    parse_opportunity_response,
    parse_relevance_response,
    parse_relationship_response,
    parse_summary_response,
)


class TestOutputParsers:
    def test_parse_summary_response(self):
        data = {
            "post_id": "abc123",
            "summary": "A post about AI hiring.",
            "key_topics": ["AI", "hiring"],
            "sentiment": "positive",
        }
        result = parse_summary_response(data)
        assert result.summary == "A post about AI hiring."
        assert "AI" in result.key_topics

    def test_parse_domain_response(self):
        data = {"domain": "technology", "confidence": 0.9, "reasoning": "Tech post"}
        result = parse_domain_response(data)
        assert result["domain"] == "technology"
        assert result["confidence"] == 0.9

    def test_parse_opportunity_response_positive(self):
        data = {
            "is_opportunity": True,
            "opportunity_type": "hiring",
            "title": "Senior Engineer Role",
            "description": "Hiring for AI team",
            "confidence_score": 0.85,
            "action_items": ["Apply"],
            "tags": ["engineering"],
        }
        result = parse_opportunity_response(data)
        assert result.is_opportunity is True
        assert result.opportunity_type == "hiring"

    def test_parse_opportunity_response_negative(self):
        result = parse_opportunity_response({"is_opportunity": False})
        assert result.is_opportunity is False

    def test_parse_relationship_response(self):
        data = {
            "person_name": "John",
            "relationship_type": "industry_peer",
            "relevance_score": 0.7,
            "mutual_connections": 5,
            "shared_interests": ["AI"],
        }
        result = parse_relationship_response(data)
        assert result.relationship_type == "industry_peer"
        assert result.relevance_score == 0.7

    def test_parse_relevance_response(self):
        data = {
            "relevance_score": 0.8,
            "reasoning": "Strong match",
            "recommended_actions": ["Reach out"],
        }
        result = parse_relevance_response(data)
        assert result["relevance_score"] == 0.8

    @patch("llm.groq.Groq")
    def test_groq_client_init(self, mock_groq):
        with patch("llm.groq.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                groq_api_key="test-key",
                groq_model="llama-3.3-70b-versatile",
                groq_temperature=0.3,
                groq_max_tokens=4096,
            )
            from llm.groq import GroqClient
            client = GroqClient()
            assert client is not None

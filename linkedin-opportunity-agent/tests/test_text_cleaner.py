from linkedin.parser import parse_post_element
from utils.text_cleaner import (
    is_generic_linkedin_post_url,
    normalize_linkedin_post_url,
    strip_linkedin_feed_noise,
)


class TestLinkedInFeedNoise:
    def test_strip_reaction_line_and_engagement_counts(self):
        raw = (
            "Somrat Dutta loves this BITS Pilani congratulates Adit Mittal on his appointment. "
            "#BITSPilani … more 378 22 1"
        )
        cleaned = strip_linkedin_feed_noise(raw, reactions_count=378, comments_count=22)
        assert "Somrat Dutta loves this" not in cleaned
        assert "378 22 1" not in cleaned
        assert "… more" not in cleaned
        assert "BITS Pilani congratulates Adit Mittal" in cleaned

    def test_generic_post_urls_are_rejected(self):
        assert is_generic_linkedin_post_url(
            "https://www.linkedin.com/company/bits-pilani-alumni-relations-official/posts/"
        )
        assert not is_generic_linkedin_post_url(
            "https://www.linkedin.com/feed/update/urn:li:activity:7123456789012345678/"
        )
        assert not is_generic_linkedin_post_url(
            "https://www.linkedin.com/posts/jane-doe_activity-7123456789012345678-AbCd"
        )

    def test_normalize_post_url(self):
        assert normalize_linkedin_post_url(
            "https://www.linkedin.com/company/foo/posts/?trk=foo"
        ) is None
        assert normalize_linkedin_post_url(
            "https://www.linkedin.com/feed/update/urn:li:activity:123/?commentUrn=abc"
        ) == "https://www.linkedin.com/feed/update/urn:li:activity:123"

    def test_parser_strips_noise_and_rejects_generic_url(self):
        raw = {
            "content": "Somrat Dutta loves this Great news for the team. … more 378 22 1",
            "author_name": "Jane Doe",
            "reactions_count": "378",
            "comments_count": "22",
            "post_url": "https://www.linkedin.com/company/foo/posts/",
        }
        post = parse_post_element(raw)
        assert post is not None
        assert "378 22 1" not in post.content
        assert post.post_url is None

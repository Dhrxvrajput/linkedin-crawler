from datetime import datetime

from database.crud import get_posts, update_post, update_post_engagement
from database.db import get_db
from utils.helpers import format_posted_time
from utils.text_cleaner import normalize_linkedin_post_url, strip_linkedin_feed_noise


class PostService:
    def get_all(self, limit: int | None = None, status: str | None = None) -> list[dict]:
        with get_db() as db:
            posts = get_posts(db, limit=limit, status=status)
            return [self._to_dict(p) for p in posts]

    def mark_engagement(self, post_id: str, engagement_status: str, error: str | None = None) -> None:
        with get_db() as db:
            update_post_engagement(db, post_id, engagement_status=engagement_status, error=error)

    def save_generated_comment(self, post_id: str, comment: str) -> None:
        with get_db() as db:
            update_post(
                db,
                post_id,
                engagement_comment=comment,
                engagement_status="comment_ready",
                engagement_updated_at=datetime.utcnow(),
                engagement_error=None,
            )

    @staticmethod
    def _to_dict(post) -> dict:
        content = strip_linkedin_feed_noise(
            post.content or "",
            reactions_count=post.reactions_count or 0,
            comments_count=post.comments_count or 0,
            author_name=post.author_name,
            author_title=post.author_title,
        )
        post_url = normalize_linkedin_post_url(post.post_url)
        return {
            "id": post.id,
            "author_name": post.author_name,
            "author_title": post.author_title,
            "author_profile_url": post.author_profile_url,
            "content": content,
            "summary": post.summary,
            "domain": post.domain,
            "reactions_count": post.reactions_count,
            "comments_count": post.comments_count,
            "post_url": post_url,
            "posted_at": post.posted_at,
            "posted_display": format_posted_time(post.posted_at),
            "scraped_at": str(post.scraped_at) if post.scraped_at else "",
            "status": post.status,
            "engagement_decision": post.engagement_decision,
            "engagement_reason": post.engagement_reason,
            "engagement_comment": post.engagement_comment,
            "engagement_status": post.engagement_status,
            "engagement_error": post.engagement_error,
        }

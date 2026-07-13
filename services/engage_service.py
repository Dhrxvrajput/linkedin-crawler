from config.settings import get_settings
from linkedin.crawler import run_manual_engagement
from schemas.post_schema import PostAuthor, PostSchema
from services.engagement_service import generate_congrats_comment
from services.post_service import PostService


async def engage_selected_posts(
    selected_posts: list[dict],
    action: str,
    dry_run: bool | None = None,
) -> dict:
    settings = get_settings()
    post_service = PostService()
    dry = settings.engagement_dry_run if dry_run is None else dry_run
    max_actions = max(1, settings.max_engagements_per_run)
    action = action.strip().lower()
    if action not in {"like", "comment"}:
        return {"processed": 0, "dry_run": dry, "results": [{"ok": False, "error": "Unsupported action"}]}

    processed = 0
    results: list[dict] = []
    for post in selected_posts[:max_actions]:
        comment_text = post.get("engagement_comment")
        if action == "comment" and not comment_text:
            comment_text = await _generate_comment_from_dict(post)
            post_service.save_generated_comment(post.get("id"), comment_text)
        result = await run_manual_engagement(
            author_name=post.get("author_name", ""),
            author_profile_url=post.get("author_profile_url"),
            content_snippet=(post.get("content", "") or "")[:120],
            action=action,
            comment_text=comment_text,
            dry_run=dry,
        )
        status = "completed" if result.get("ok") else "failed"
        if dry and result.get("ok"):
            status = "dry_run"
        post_service.mark_engagement(post.get("id"), engagement_status=status, error=result.get("error"))
        results.append({"post_id": post.get("id"), "action": action, **result})
        processed += 1

    return {
        "processed": processed,
        "dry_run": dry,
        "results": results,
    }


async def generate_comments_for_posts(selected_posts: list[dict]) -> dict:
    post_service = PostService()
    generated = 0
    results = []
    for post in selected_posts:
        comment = await _generate_comment_from_dict(post)
        post_service.save_generated_comment(post.get("id"), comment)
        results.append({"post_id": post.get("id"), "comment": comment})
        generated += 1
    return {"generated": generated, "results": results}


async def _generate_comment_from_dict(post: dict) -> str:
    schema = PostSchema(
        id=post.get("id"),
        author=PostAuthor(
            name=post.get("author_name") or "LinkedIn User",
            title=post.get("author_title"),
            profile_url=post.get("author_profile_url"),
        ),
        content=post.get("content") or "",
        summary=post.get("summary"),
        reactions_count=post.get("reactions_count") or 0,
        comments_count=post.get("comments_count") or 0,
    )
    return await generate_congrats_comment(schema)

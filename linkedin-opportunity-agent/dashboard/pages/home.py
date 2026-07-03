import streamlit as st

from dashboard.components.digest_view import render_digest
from dashboard.components.scrollable_feed import render_scrollable_posts
from database.crud import count_posts, get_opportunities, get_posts
from database.db import get_db
from services.digest_service import DigestService
from services.engage_service import engage_selected_posts, generate_comments_for_posts
from services.post_service import PostService


def render():
    st.title("LinkedIn Opportunity Operator")
    st.markdown("Analyze feed and run engagement actions only when you approve.")

    digest_service = DigestService()
    post_service = PostService()
    st.session_state.setdefault("engage_results", [])

    with get_db() as db:
        all_opps = get_opportunities(db, limit=1000, min_score=0.0)
        total_posts = count_posts(db)
        all_posts = get_posts(db, limit=None)
        total_opps = len(all_opps)
        new_count = sum(1 for o in all_opps if o.status == "new")
        avg_score = sum(o.relevance_score for o in all_opps) / max(total_opps, 1)
        last_scraped = str(all_posts[0].scraped_at)[:16] if all_posts else "Never"
        comment_ready = sum(1 for p in all_posts if (p.engagement_comment or "").strip())
        engagement_done = sum(1 for p in all_posts if (p.engagement_status or "") == "completed")

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("Posts in DB", total_posts)
    with col2:
        st.metric("Opportunities", total_opps)
    with col3:
        st.metric("New", new_count)
    with col4:
        st.metric("Avg Score", f"{avg_score:.0%}")
    with col5:
        st.metric("Last Crawl", last_scraped)
    with col6:
        st.metric("Comments Ready", comment_ready)
    with col7:
        st.metric("Engaged", engagement_done)

    st.divider()

    tab_feed, tab_engage, tab_digest = st.tabs(["LinkedIn Feed", "Manual Engage", "Daily Digest"])

    with tab_feed:
        posts = post_service.get_all(limit=None)
        st.caption(f"Showing all {len(posts)} posts in database")
        c1, c2 = st.columns([1, 1])
        with c1:
            comment_filter = st.selectbox("Comment text", ["all", "with comment", "without comment"], index=0)
        with c2:
            status_filter = st.selectbox("Engagement status", ["all", "pending", "dry_run", "completed", "failed"], index=0)

        if comment_filter == "with comment":
            posts = [p for p in posts if (p.get("engagement_comment") or "").strip()]
        elif comment_filter == "without comment":
            posts = [p for p in posts if not (p.get("engagement_comment") or "").strip()]
        if status_filter != "all":
            posts = [p for p in posts if (p.get("engagement_status") or "pending") == status_filter]

        render_scrollable_posts(
            posts,
            height=650,
            empty_message="No posts yet. Click **Crawl LinkedIn Feed** below to fetch your latest posts.",
        )

    with tab_engage:
        posts = post_service.get_all(limit=None)
        if not posts:
            st.info("No posts yet. Crawl feed first.")
        else:
            st.caption("No suggestions are auto-generated. You choose the posts and action.")
            options = {
                f"{p['author_name']} | {p['posted_display']}": p["id"]
                for p in posts
            }
            selected_labels = st.multiselect("Select posts to engage", list(options.keys()))
            selected_posts = [p for p in posts if p["id"] in {options[s] for s in selected_labels}]

            dry_run = st.toggle("Dry run (simulation only)", value=False)
            if dry_run:
                st.warning("Dry run is ON: likes/comments will not be posted to LinkedIn.")
            st.caption("Generate creates text only. Posting comments/likes needs separate manual buttons.")
            b1, b2, b3 = st.columns(3)
            with b1:
                generate_click = st.button("Generate AI Comment", use_container_width=True)
            with b2:
                comment_click = st.button("Post Generated Comment", type="primary", use_container_width=True)
            with b3:
                like_click = st.button("Like Selected Posts", use_container_width=True)

            if generate_click:
                if not selected_posts:
                    st.warning("Select at least one post.")
                else:
                    import asyncio
                    result = asyncio.run(generate_comments_for_posts(selected_posts))
                    st.success(f"Generated comments for {result['generated']} post(s).")
                    for r in result["results"]:
                        st.write(f"{r.get('post_id', '')}: {r.get('comment', '')}")
                    st.info("Generated comments are saved to DB and visible in the feed cards.")

            if like_click:
                if not selected_posts:
                    st.warning("Select at least one post.")
                else:
                    import asyncio
                    result = asyncio.run(engage_selected_posts(selected_posts, action="like", dry_run=dry_run))
                    st.session_state["engage_results"] = result["results"]
                    st.success(
                        f"Processed {result['processed']} like action(s) "
                        f"({'dry run' if result['dry_run'] else 'live'})."
                    )
                    for r in result["results"]:
                        label = f"LIKE | {r.get('post_id', '')}"
                        if r.get("ok"):
                            st.write(f"{label}: {r.get('status', 'ok')}")
                        else:
                            st.error(f"{label}: {r.get('error', 'failed')}")

            if comment_click:
                if not selected_posts:
                    st.warning("Select at least one post.")
                else:
                    import asyncio
                    result = asyncio.run(engage_selected_posts(selected_posts, action="comment", dry_run=dry_run))
                    st.session_state["engage_results"] = result["results"]
                    st.success(
                        f"Processed {result['processed']} comment action(s) "
                        f"({'dry run' if result['dry_run'] else 'live'})."
                    )
                    for r in result["results"]:
                        label = f"COMMENT | {r.get('post_id', '')}"
                        if r.get("ok"):
                            st.write(f"{label}: {r.get('status', 'ok')}")
                        else:
                            st.error(f"{label}: {r.get('error', 'failed')}")

            if st.session_state["engage_results"]:
                with st.expander("Last engagement result details", expanded=True):
                    for r in st.session_state["engage_results"]:
                        st.write(r)

    with tab_digest:
        render_digest(digest_service.get_latest() or digest_service.generate_summary(), height=650)

    st.divider()

    col_crawl, col_agent, col_refresh = st.columns(3)

    with col_crawl:
        if st.button("Crawl LinkedIn Feed", type="primary", use_container_width=True):
            with st.spinner("Crawling your latest LinkedIn feed..."):
                import asyncio
                from app import crawl_feed
                result = asyncio.run(crawl_feed(user_id=st.session_state.get("user", {}).get("id")))
                st.success(
                    f"Fetched {result['posts_fetched']} posts and saved {result['posts_saved']} to the database."
                )
                st.rerun()

    with col_agent:
        if st.button("Run Full Agent", use_container_width=True):
            with st.spinner("Crawling + analyzing with AI (this takes a few minutes)..."):
                import asyncio
                from app import run_agent
                result = asyncio.run(run_agent())
                st.success(
                    f"Done! Processed {result.get('processed_count', 0)} posts, "
                    f"found {len(result.get('opportunities', []))} opportunities."
                )
                st.rerun()

    with col_refresh:
        if st.button("Reload Dashboard", use_container_width=True):
            st.rerun()

    st.caption(
        "**Crawl LinkedIn Feed** pulls fresh posts from LinkedIn (fast). "
        "**Run Full Agent** also runs AI analysis. "
        "**Reload Dashboard** only refreshes the page from the database."
    )

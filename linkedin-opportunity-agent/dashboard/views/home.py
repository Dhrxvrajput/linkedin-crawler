import streamlit as st

from dashboard.components.digest_view import render_digest
from dashboard.components.scrollable_feed import render_scrollable_posts
from database.crud import count_posts, get_opportunities, get_posts
from database.db import get_db
from services.digest_service import DigestService
from services.engage_service import engage_selected_posts, generate_comments_for_posts
from services.post_service import PostService


def render():
    st.title("Your LinkedIn Feed")
    st.markdown("Browse posts, generate comments, and engage when you're ready.")

    digest_service = DigestService()
    post_service = PostService()
    st.session_state.setdefault("engage_results", [])

    with get_db() as db:
        all_opps = get_opportunities(db, limit=1000, min_score=0.0)
        total_posts = count_posts(db)
        all_posts = get_posts(db, limit=None)
        total_opps = len(all_opps)
        new_count = sum(1 for o in all_opps if o.status == "new")
        last_updated_dt = all_posts[0].scraped_at if all_posts else None
        comment_ready = sum(1 for p in all_posts if (p.engagement_comment or "").strip())
        engagement_done = sum(1 for p in all_posts if (p.engagement_status or "") == "completed")

    col1, col2, col3, col5, col6 = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.metric("Posts", total_posts)
    with col2:
        st.metric("Opportunities", total_opps)
    with col3:
        st.metric("New", new_count)
    with col5:
        st.metric("Draft Comments", comment_ready)
    with col6:
        st.metric("Engaged", engagement_done)

    st.divider()

    tab_feed, tab_engage, tab_digest = st.tabs(["Feed", "Engage", "Daily Digest"])

    with tab_feed:
        posts = post_service.get_all(limit=None)
        st.caption(f"{len(posts)} posts")
        c1, c2 = st.columns([1, 1])
        with c1:
            comment_filter = st.selectbox(
                "Comments",
                ["All posts", "With draft comment", "Without draft comment"],
                index=0,
            )
        with c2:
            status_filter = st.selectbox(
                "Status",
                ["All", "Not started", "Comment ready", "Done", "Could not complete"],
                index=0,
            )

        status_map = {
            "Not started": "pending",
            "Comment ready": "comment_ready",
            "Done": "completed",
            "Could not complete": "failed",
        }

        if comment_filter == "With draft comment":
            posts = [p for p in posts if (p.get("engagement_comment") or "").strip()]
        elif comment_filter == "Without draft comment":
            posts = [p for p in posts if not (p.get("engagement_comment") or "").strip()]
        if status_filter != "All":
            posts = [p for p in posts if (p.get("engagement_status") or "pending") == status_map[status_filter]]

        render_scrollable_posts(
            posts,
            height=650,
            empty_message="No posts yet. Click **Update from LinkedIn** to fetch your latest feed.",
        )

    with tab_engage:
        posts = post_service.get_all(limit=None)
        if not posts:
            st.info("No posts yet. Update your feed from LinkedIn first.")
        else:
            st.caption("Select posts, generate a comment, edit it, then post when you approve.")
            
            # Initialize session state for generated comments
            if "generated_comments" not in st.session_state:
                st.session_state.generated_comments = {}
            
            options = {
                f"{p['author_name']} · {p['posted_display']}": p["id"]
                for p in posts
            }
            selected_labels = st.multiselect("Choose posts", list(options.keys()))
            selected_posts = [p for p in posts if p["id"] in {options[s] for s in selected_labels}]

            b1, b2, b3 = st.columns(3)
            with b1:
                generate_click = st.button("Generate AI Comment", use_container_width=True)
            with b2:
                comment_click = st.button("Post Comment", type="primary", use_container_width=True)
            with b3:
                like_click = st.button("Like Post", use_container_width=True)

            if generate_click:
                if not selected_posts:
                    st.warning("Choose at least one post.")
                else:
                    import asyncio

                    with st.spinner("Generating comments with AI..."):
                        result = asyncio.run(generate_comments_for_posts(selected_posts))
                    st.success(f"Generated {result['generated']} comment(s).")
                    # Store generated comments in session state
                    for r in result["results"]:
                        post_id = r.get("post_id")
                        comment = r.get("comment", "")
                        st.session_state.generated_comments[post_id] = comment

            # Display editable comment boxes for selected posts
            if selected_posts and st.session_state.generated_comments:
                st.divider()
                st.subheader("Edit Comments")
                for post in selected_posts:
                    post_id = post["id"]
                    if post_id in st.session_state.generated_comments:
                        st.write(f"📝 **{post['author_name']}** · {post['posted_display']}")
                        edited_comment = st.text_area(
                            f"Comment for post {post_id[:8]}",
                            value=st.session_state.generated_comments[post_id],
                            height=100,
                            label_visibility="collapsed",
                            key=f"comment_{post_id}"
                        )
                        # Update the comment in session state as user edits
                        st.session_state.generated_comments[post_id] = edited_comment

            if like_click:
                if not selected_posts:
                    st.warning("Choose at least one post.")
                else:
                    import asyncio

                    with st.spinner("Liking posts..."):
                        result = asyncio.run(engage_selected_posts(selected_posts, action="like", dry_run=False))
                    st.session_state["engage_results"] = result["results"]
                    if result["processed"]:
                        st.success(f"Liked {result['processed']} post(s).")
                    for r in result["results"]:
                        if not r.get("ok"):
                            st.error(r.get("error", "Something went wrong."))

            if comment_click:
                if not selected_posts:
                    st.warning("Choose at least one post.")
                else:
                    # Use edited comments from session state
                    posts_with_comments = []
                    for post in selected_posts:
                        post_id = post["id"]
                        if post_id in st.session_state.generated_comments:
                            post_copy = post.copy()
                            post_copy["engagement_comment"] = st.session_state.generated_comments[post_id]
                            posts_with_comments.append(post_copy)
                        else:
                            posts_with_comments.append(post)
                    
                    if not posts_with_comments:
                        st.warning("Generate comments first before posting.")
                    else:
                        import asyncio

                        with st.spinner("Posting comments..."):
                            result = asyncio.run(engage_selected_posts(posts_with_comments, action="comment", dry_run=False))
                        st.session_state["engage_results"] = result["results"]
                        if result["processed"]:
                            st.success(f"Posted {result['processed']} comment(s).")
                            # Clear the generated comments after posting
                            for post in posts_with_comments:
                                if post["id"] in st.session_state.generated_comments:
                                    del st.session_state.generated_comments[post["id"]]
                        for r in result["results"]:
                            if not r.get("ok"):
                                st.error(r.get("error", "Something went wrong."))

    with tab_digest:
        render_digest(digest_service.get_latest() or digest_service.generate_summary(), height=650)

    st.divider()

    col_crawl, col_agent, col_refresh = st.columns(3)

    with col_crawl:
        if st.button("Update from LinkedIn", type="primary", use_container_width=True):
            with st.spinner("Fetching your latest posts..."):
                import asyncio
                from app import crawl_feed

                result = asyncio.run(crawl_feed(user_id=st.session_state.get("user", {}).get("id")))
                st.success(f"Updated {result['posts_saved']} posts from your feed.")
                st.rerun()

    with col_agent:
        if st.button("Analyze with AI", use_container_width=True):
            with st.spinner("Analyzing your feed..."):
                import asyncio
                from app import run_agent

                result = asyncio.run(run_agent())
                st.success(
                    f"Found {len(result.get('opportunities', []))} opportunities "
                    f"from {result.get('processed_count', 0)} posts."
                )
                st.rerun()

    with col_refresh:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

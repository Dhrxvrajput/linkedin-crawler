import streamlit as st

from dashboard.components.digest_view import render_digest
from dashboard.components.scrollable_feed import render_scrollable_posts
from database.crud import count_posts, get_opportunities, get_posts
from database.db import get_db
from services.digest_service import DigestService
from services.engage_service import engage_selected_posts, generate_comments_for_posts
from services.post_service import PostService


def render():
    # ── Hero header ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(108,99,255,.12) 0%, rgba(99,179,237,.08) 100%);
            border: 1px solid rgba(108,99,255,.12);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.2rem;
        ">
            <h2 style="margin:0 0 .3rem; font-weight:700; color:#E8E8ED;">
                Your LinkedIn Feed
            </h2>
            <p style="margin:0; color:#9D9DB7; font-size:.9rem;">
                Browse posts according to your profile, and engage when you're ready.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    # ── Metric cards ──────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="dashboard-metrics-grid">
          <!-- Card 1: Posts -->
          <div class="dashboard-metric-card">
            <div class="metric-icon-wrapper blue">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-file-text"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
            </div>
            <div class="metric-content">
              <span class="metric-title">Posts</span>
              <h3 class="metric-num">{total_posts}</h3>
            </div>
          </div>

          <!-- Card 2: Opportunities -->
          <div class="dashboard-metric-card">
            <div class="metric-icon-wrapper target">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-target"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
            </div>
            <div class="metric-content">
              <span class="metric-title">Opportunities</span>
              <h3 class="metric-num">{total_opps}</h3>
            </div>
          </div>

          <!-- Card 3: New -->
          <div class="dashboard-metric-card">
            <div class="metric-icon-wrapper yellow">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="m5 3 1 2.5L8.5 6 6 7 5 9.5 4 7 1.5 6 4 5 5 3Z"/><path d="m19 17 1 2.5 2.5.5-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1 1-2.5Z"/></svg>
            </div>
            <div class="metric-content">
              <span class="metric-title">New</span>
              <h3 class="metric-num">{new_count}</h3>
            </div>
          </div>

          <!-- Card 4: Draft Comments -->
          <div class="dashboard-metric-card">
            <div class="metric-icon-wrapper purple">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-messages-square"><path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2v5Z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/></svg>
            </div>
            <div class="metric-content">
              <span class="metric-title">Draft Comments</span>
              <h3 class="metric-num">{comment_ready}</h3>
            </div>
          </div>

          <!-- Card 5: Engaged -->
          <div class="dashboard-metric-card">
            <div class="metric-icon-wrapper green">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-check"><path d="M4 12v.01"/><path d="M20 6 9 17l-5-5"/><path d="m20 12-11 11-4-4"/></svg>
            </div>
            <div class="metric-content">
              <span class="metric-title">Engaged</span>
              <h3 class="metric-num">{engagement_done}</h3>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")  # spacer

    # ── Tabs ──────────────────────────────────────────────────────────────────
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
            empty_message="No posts yet. Click **Refresh from LinkedIn** in the sidebar to fetch your latest feed.",
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
                generate_click = st.button("✨ Generate AI Comment", use_container_width=True)
            with b2:
                comment_click = st.button("💬 Post Comment", type="primary", use_container_width=True)
            with b3:
                like_click = st.button("👍 Like Post", use_container_width=True)

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
                st.subheader("✏️ Edit Comments")
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

    # ── Background Task Monitoring & Actions ───────────────────────────────────
    from services.task_runner import task_registry
    import time

    crawl_status = task_registry.get_task_status("crawl_feed")
    agent_status = task_registry.get_task_status("run_agent")
    
    any_running = False

    # Render Task Progress overlays
    if crawl_status:
        if crawl_status["status"] == "running":
            any_running = True
            st.info(f"🔄 **Update from LinkedIn is running in background...**\n\n*Current step:* `{crawl_status['progress']}`")
        elif crawl_status["status"] == "success":
            res = crawl_status["result"]
            st.success(f"✅ Updated {res.get('posts_saved', 0)} posts from your feed.")
            task_registry.clear_task("crawl_feed")
            time.sleep(1.5)
            st.rerun()
        elif crawl_status["status"] == "error":
            st.error(f"❌ LinkedIn update failed: {crawl_status['error']}")
            task_registry.clear_task("crawl_feed")
            
    if agent_status:
        if agent_status["status"] == "running":
            any_running = True
            st.info(f"🧠 **AI Agent Analysis is running in background...**\n\n*Current step:* `{agent_status['progress']}`")
        elif agent_status["status"] == "success":
            res = agent_status["result"]
            st.success(
                f"✅ AI Analysis complete! Found {len(res.get('opportunities', []))} opportunities "
                f"from {res.get('processed_count', 0)} posts."
            )
            task_registry.clear_task("run_agent")
            time.sleep(2)
            st.rerun()
        elif agent_status["status"] == "error":
            st.error(f"❌ AI analysis failed: {agent_status['error']}")
            task_registry.clear_task("run_agent")

    # ── Action buttons ────────────────────────────────────────────────────────
    col_crawl, col_agent, col_refresh = st.columns(3)

    with col_crawl:
        if st.button("🔄 Update from LinkedIn", type="primary", use_container_width=True, disabled=any_running):
            from app import crawl_feed
            user_id = st.session_state.get("user", {}).get("id")
            task_registry.start_task("crawl_feed", crawl_feed, user_id=user_id)
            st.rerun()

    with col_agent:
        if st.button("🧠 Analyze with AI", use_container_width=True, disabled=any_running):
            from app import run_agent
            task_registry.start_task("run_agent", run_agent)
            st.rerun()

    with col_refresh:
        if st.button("🔃 Refresh", use_container_width=True):
            st.rerun()

    # Trigger automatic UI refresh if status is running
    if any_running:
        time.sleep(2)
        st.rerun()

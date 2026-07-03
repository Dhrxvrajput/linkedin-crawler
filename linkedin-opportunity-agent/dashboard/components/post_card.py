import streamlit as st


def render_post_card(post):
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{post.get('author_name', 'Unknown')}**")
            if post.get("author_title"):
                st.caption(post["author_title"])
        with col2:
            if post.get("domain"):
                st.badge(post["domain"])

        posted = post.get("posted_display") or "Posted time unknown"
        st.caption(f"Posted: {posted}")
        if post.get("scraped_at"):
            st.caption(f"Crawled: {post['scraped_at'][:16]}")

        status = (post.get("engagement_status") or "pending").upper()
        st.caption(f"Engagement status: {status}")
        if post.get("engagement_comment"):
            st.code(post["engagement_comment"], language=None)

        summary = post.get("summary")
        if summary:
            st.markdown("**Summary**")
            st.info(summary)
        else:
            st.markdown("**Preview**")
            preview = post.get("content", "")
            st.markdown(preview[:300] + ("..." if len(preview) > 300 else ""))

        with st.expander("Full post"):
            st.markdown(post.get("content", ""))

        metrics_cols = st.columns(4)
        with metrics_cols[0]:
            st.metric("Reactions", post.get("reactions_count", 0))
        with metrics_cols[1]:
            st.metric("Comments", post.get("comments_count", 0))
        with metrics_cols[2]:
            if post.get("post_url"):
                st.link_button("View Post", post["post_url"], use_container_width=True)
            else:
                st.caption("No post link")
        with metrics_cols[3]:
            if post.get("author_profile_url"):
                st.link_button("Profile", post["author_profile_url"], use_container_width=True)

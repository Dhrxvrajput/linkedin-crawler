import streamlit as st

_STATUS_LABELS = {
    "pending": "Not started",
    "comment_ready": "Comment ready",
    "completed": "Done",
    "failed": "Could not complete",
}


def render_post_card(post):
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{post.get('author_name', 'Unknown')}**")
            if post.get("author_title"):
                st.caption(post["author_title"])
        with col2:
            if post.get("domain"):
                st.info(f"Domain: {post['domain']}")

        posted = post.get("posted_display") or "Time unknown"
        st.caption(f"🗓️ {posted}")

        status = post.get("engagement_status") or "pending"
        
        # AI Section at the top
        if post.get("engagement_comment") or post.get("summary"):
            with st.container(border=True):
                st.markdown("🔍 **AI Analysis**")
                
                if post.get("engagement_comment"):
                    st.success(f"**AI Draft Comment:** {post['engagement_comment']}")
                    label = _STATUS_LABELS.get(status, status.replace("_", " ").title())
                    st.caption(f"Status: {label}")
                
                if post.get("summary"):
                    st.markdown("**Summary**")
                    st.write(post["summary"])

        st.divider()
        st.markdown("📄 **Post Content**")
        content = post.get("content", "")
        limit = 1200
        if len(content) > limit:
            # Find the last space before the limit to avoid breaking words
            split_idx = content.rfind(" ", 0, limit)
            if split_idx == -1:
                split_idx = limit
            
            st.markdown(content[:split_idx] + "...")
            with st.expander("Show more"):
                st.markdown(content[split_idx:].strip())
        else:
            st.markdown(content)

        metrics_cols = st.columns(3)
        with metrics_cols[0]:
            st.metric("Reactions", post.get("reactions_count", 0))
        with metrics_cols[1]:
            st.metric("Comments", post.get("comments_count", 0))
        with metrics_cols[2]:
            if post.get("author_profile_url"):
                st.link_button("View profile", post["author_profile_url"], use_container_width=True)

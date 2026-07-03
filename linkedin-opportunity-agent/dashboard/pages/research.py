import streamlit as st

from dashboard.components.digest_view import render_digest
from dashboard.components.scrollable_feed import render_scrollable_posts
from services.digest_service import DigestService
from services.post_service import PostService


def render():
    st.title("Research")

    post_service = PostService()
    digest_service = DigestService()

    tab1, tab2, tab3 = st.tabs(["Posts", "Digest", "Export"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            domain_filter = st.selectbox(
                "Domain",
                ["all", "technology", "finance", "healthcare", "education", "marketing", "sales", "product", "design", "other"],
            )
        with col2:
            if st.button("Refresh posts", use_container_width=True):
                st.rerun()

        posts = post_service.get_all(limit=None)
        if domain_filter != "all":
            posts = [p for p in posts if p.get("domain") == domain_filter]

        render_scrollable_posts(posts, height=650)

    with tab2:
        digest = digest_service.get_latest() or digest_service.generate_summary()
        render_digest(digest, height=650)

        if st.button("Regenerate Digest"):
            digest = digest_service.generate_summary()
            render_digest(digest, height=650)

    with tab3:
        if st.button("Export Digest to File"):
            path = digest_service.export_digest()
            st.success(f"Exported to {path}")

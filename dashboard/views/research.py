import streamlit as st

from dashboard.components.digest_view import render_digest
from dashboard.components.scrollable_feed import render_scrollable_posts
from services.digest_service import DigestService
from services.post_service import PostService


def render():
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(10, 102, 194, 0.08) 0%, rgba(99, 179, 237, 0.04) 100%);
            border: 1px solid rgba(10, 102, 194, 0.12);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.2rem;
        ">
            <h2 style="margin:0 0 .3rem; font-weight:700; color:#E8E8ED; display:flex; align-items:center; gap:8px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flask-conical"><path d="M10 2v7.586a2 2 0 0 1-.586 1.414l-5.69 5.69A2 2 0 0 0 5.138 20h13.724a2 2 0 0 0 1.414-3.414l-5.69-5.69A2 2 0 0 1 13.586 9.586V2"/><path d="M8 2h8"/><path d="M6 16h12"/></svg>
                Research
            </h2>
            <p style="margin:0; color:#9D9DB7; font-size:.9rem;">
                Deep-dive into posts, digests, and export insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown(
            """
            <div style="
                text-align:center;
                padding: 2rem 1rem;
                color:#9D9DB7;
            ">
                <div style="display:flex; justify-content:center; color:#0A66C2; margin-bottom:12px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-share-2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/></svg>
                </div>
                <p>Export your daily digest to a text file for offline reading or sharing.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Export Digest to File", use_container_width=True):
            path = digest_service.export_digest()
            st.success(f"Exported to `{path}`")

import streamlit as st

from dashboard.components.post_card import render_post_card


def render_scrollable_posts(posts: list[dict], height: int = 600, empty_message: str = "No posts yet."):
    if not posts:
        st.markdown(
            f"""
            <div style="
                text-align:center;
                padding: 3rem 1rem;
                color:#9D9DB7;
            ">
                <div style="font-size:2.5rem; margin-bottom:.8rem;">📭</div>
                <p style="font-size:.9rem;">{empty_message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.caption(f"📰 {len(posts)} posts — scroll to browse")
    with st.container(height=height, border=False):
        for post in posts:
            render_post_card(post)

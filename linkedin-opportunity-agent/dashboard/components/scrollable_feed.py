import streamlit as st

from dashboard.components.post_card import render_post_card


def render_scrollable_posts(posts: list[dict], height: int = 600, empty_message: str = "No posts yet."):
    if not posts:
        st.info(empty_message)
        return

    st.caption(f"{len(posts)} posts — scroll to browse")
    with st.container(height=height, border=True):
        for post in posts:
            render_post_card(post)

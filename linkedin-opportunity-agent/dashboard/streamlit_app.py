import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from database.db import setup_database

st.set_page_config(
    page_title="LinkedIn Opportunity Agent",
    page_icon="LI",
    layout="wide",
    initial_sidebar_state="expanded",
)

setup_database()
settings = get_settings()

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 1rem;}
    .stMetric {border: 1px solid rgba(120,120,120,.2); border-radius: 10px; padding: 8px 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)

if settings.auth_required and not st.session_state.get("authenticated"):
    from dashboard.pages import login

    login.render()
    st.stop()

user = st.session_state.get("user")
if settings.auth_required and user and not user.get("linkedin_connected"):
    from dashboard.pages import connect_linkedin

    connect_linkedin.render()
    st.stop()

PAGES = {
    "Home": "dashboard.pages.home",
    "Opportunities": "dashboard.pages.opportunities",
    "People Radar": "dashboard.pages.people_radar",
    "Research": "dashboard.pages.research",
    "Settings": "dashboard.pages.settings",
}

st.sidebar.title("LinkedIn Control")
user = st.session_state.get("user")
if user:
    st.sidebar.caption(f"Signed in as **{user.get('name') or user.get('email')}**")

selection = st.sidebar.radio("Navigate", list(PAGES.keys()))

st.sidebar.caption("Manual engagement only: no automatic likes/comments.")

if st.sidebar.button("Reload from DB"):
    st.rerun()

if st.sidebar.button("Crawl LinkedIn Feed"):
    import asyncio
    from app import crawl_feed

    user_id = user.get("id") if user else None
    with st.spinner("Crawling LinkedIn..."):
        asyncio.run(crawl_feed(user_id=user_id))
    st.rerun()

if settings.auth_required and st.sidebar.button("Log out"):
    st.session_state.pop("authenticated", None)
    st.session_state.pop("user", None)
    st.rerun()

st.sidebar.info("Use Home page buttons to manually generate AI comments or like selected posts.")

module = __import__(PAGES[selection], fromlist=["render"])
module.render()

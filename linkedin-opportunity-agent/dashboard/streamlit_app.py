import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import BASE_DIR, get_settings
from database.db import setup_database

st.set_page_config(
    page_title="LinkedIn Opportunity Agent",
    page_icon="🔗",
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

# Initialize session state with persistence
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

# Try to recover session from URL parameter or restore last user
session_file = BASE_DIR / "storage" / "last_session.txt"

if settings.auth_required and not st.session_state.get("authenticated"):
    query_params = st.query_params
    user_id_to_recover = query_params.get("user_id")
    
    # If no URL param, try the local 'Remember Me' file
    if not user_id_to_recover and session_file.exists():
        try:
            user_id_to_recover = session_file.read_text().strip()
        except Exception:
            pass

    if user_id_to_recover:
        from database.db import get_db
        from database.models import AppUser
        
        try:
            with get_db() as db_session:
                user = db_session.query(AppUser).filter(AppUser.id == user_id_to_recover).first()
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "linkedin_connected": user.linkedin_connected,
                    }
        except Exception:
            pass

if settings.auth_required and not st.session_state.get("authenticated"):
    from dashboard.views import login

    login.render()
    st.stop()

user = st.session_state.get("user")
if settings.auth_required and user and not user.get("linkedin_connected"):
    from dashboard.views import connect_linkedin

    connect_linkedin.render()
    st.stop()

PAGES = {
    "Home": "dashboard.views.home",
    "Opportunities": "dashboard.views.opportunities",
    "People Radar": "dashboard.views.people_radar",
    "Research": "dashboard.views.research",
    "Settings": "dashboard.views.settings",
}

st.sidebar.title("LinkedIn Agent")
if user:
    st.sidebar.caption(f"Hello, **{user.get('name') or user.get('email')}**")

selection = st.sidebar.radio("Menu", list(PAGES.keys()))

if st.sidebar.button("Refresh from LinkedIn", use_container_width=True):
    import asyncio
    from app import crawl_feed

    user_id = user.get("id") if user else None
    with st.spinner("Fetching your latest posts..."):
        asyncio.run(crawl_feed(user_id=user_id))
    st.rerun()

if settings.auth_required and st.sidebar.button("Log out", use_container_width=True):
    # Clear session state
    st.session_state.clear()
    # Clear query parameters to prevent automatic re-login
    st.query_params.clear()
    st.rerun()

module = __import__(PAGES[selection], fromlist=["render"])
module.render()

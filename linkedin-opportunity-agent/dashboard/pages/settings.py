import streamlit as st
from pathlib import Path

from config.settings import get_settings


def render():
    st.title("Settings")

    settings = get_settings()

    st.subheader("User Profile")
    st.text_input("Name", value=settings.user_name, disabled=True, key="user_name")
    st.text_input("Title", value=settings.user_title, disabled=True, key="user_title")
    st.text_input("Company", value=settings.user_company, disabled=True, key="user_company")
    st.text_area("Interests (comma-separated)", value=settings.user_interests, disabled=True)
    st.text_area("Skills (comma-separated)", value=settings.user_skills, disabled=True)

    st.info("Update these values in your `.env` file and restart the app.")

    st.divider()

    st.subheader("Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Groq Model", value=settings.groq_model, disabled=True)
        st.number_input("Max Posts", value=settings.linkedin_max_posts, disabled=True)
        st.number_input("Digest Top N", value=settings.digest_top_n, disabled=True)
        st.number_input("Max Engagements / Run", value=settings.max_engagements_per_run, disabled=True)
    with col2:
        st.text_input("Database", value=settings.database_url, disabled=True)
        st.slider("Opportunity Threshold", value=settings.opportunity_score_threshold, disabled=True)
        st.slider("Relevance Threshold", value=settings.relevance_score_threshold, disabled=True)
        st.number_input("Comment Max Chars", value=settings.comment_max_chars, disabled=True)

    st.divider()

    st.subheader("LinkedIn")
    st.caption("Crawls always run **headless** (no browser window). Use `python app.py --login` once if you need to sign in manually.")
    st.caption("Auto-like: disabled by default | Auto-comment: disabled by default | Actions require manual trigger in dashboard.")
    profile_path = Path(settings.linkedin_browser_profile)
    if profile_path.exists():
        st.success(f"Browser profile found: `{profile_path}`")
    else:
        st.warning("No browser profile yet. Run `python app.py --login` first.")

    st.divider()

    st.subheader("LinkedIn Session")
    session_path = Path(settings.linkedin_session_path)
    if session_path.exists():
        st.success(f"Session file found: `{session_path}`")
    else:
        st.warning("No LinkedIn session found. Run the agent to log in.")

    st.divider()

    st.subheader("Database")
    if st.button("Initialize Database"):
        from database.db import setup_database
        setup_database()
        st.success("Database initialized successfully!")

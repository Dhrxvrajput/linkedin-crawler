import streamlit as st

from config.settings import get_settings
from database.db import get_db
from database.models import AppUser
from services.user_linkedin_service import connect_user_linkedin


def render():
    st.title("Settings")

    settings = get_settings()
    user = st.session_state.get("user") or {}

    st.subheader("Account")
    if user:
        st.text_input("Email", value=user.get("email", ""), disabled=True)
        st.text_input("Name", value=user.get("name", ""), disabled=True)
        if user.get("linkedin_connected"):
            st.success("LinkedIn is connected.")
        else:
            st.warning("LinkedIn is not connected yet.")

    st.divider()

    st.subheader("Your profile")
    
    # Load current profile data from database
    profile_data = {
        "title": "",
        "company": "",
        "interests": "",
        "skills": "",
    }
    
    if user and user.get("id"):
        try:
            with get_db() as db:
                user_profile = db.query(AppUser).filter(AppUser.id == user.get("id")).first()
                if user_profile:
                    # Extract values while inside session context
                    profile_data = {
                        "title": getattr(user_profile, "user_title", None) or "",
                        "company": getattr(user_profile, "user_company", None) or "",
                        "interests": getattr(user_profile, "user_interests", None) or "",
                        "skills": getattr(user_profile, "user_skills", None) or "",
                    }
        except Exception:
            pass
    
    # Display editable profile fields using extracted data
    new_title = st.text_input(
        "Job title",
        value=profile_data["title"],
        key="user_title"
    )
    new_company = st.text_input(
        "Company",
        value=profile_data["company"],
        key="user_company"
    )
    new_interests = st.text_area(
        "Interests",
        value=profile_data["interests"],
        key="user_interests"
    )
    new_skills = st.text_area(
        "Skills",
        value=profile_data["skills"],
        key="user_skills"
    )
    
    if st.button("Save Profile", type="primary", use_container_width=True):
        if user and user.get("id"):
            try:
                with get_db() as db:
                    app_user = db.query(AppUser).filter(AppUser.id == user.get("id")).first()
                    if app_user:
                        # Update attributes and commit within session
                        app_user.user_title = new_title or None
                        app_user.user_company = new_company or None
                        app_user.user_interests = new_interests or None
                        app_user.user_skills = new_skills or None
                        # Commit happens automatically on context exit
                st.success("Profile updated successfully!")
            except Exception as e:
                st.error(f"Failed to save profile: {e}")
        else:
            st.error("Please log in first.")

    st.divider()

    st.subheader("LinkedIn")
    if user.get("linkedin_connected"):
        st.success("Your LinkedIn account is linked.")
        if st.button("Reconnect LinkedIn"):
            import asyncio

            with st.spinner("Opening LinkedIn..."):
                ok, message = asyncio.run(connect_user_linkedin(user["id"]))
            if ok:
                st.success("LinkedIn reconnected.")
            else:
                st.error(message)
    else:
        st.warning("Connect LinkedIn from the onboarding screen to use the feed.")

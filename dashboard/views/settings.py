import streamlit as st

from config.settings import get_settings
from database.db import get_db
from database.models import AppUser
from services.user_linkedin_service import connect_user_linkedin


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
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-settings"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
                Settings
            </h2>
            <p style="margin:0; color:#9D9DB7; font-size:.9rem;">
                Manage your account, profile, and LinkedIn connection.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    settings = get_settings()
    user = st.session_state.get("user") or {}

    # ── Account Section ──────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-weight:600; font-size:1rem; color:#E8E8ED; margin-bottom:.5rem; display:flex; align-items:center; gap:6px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A66C2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-user"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Account
        </div>
        """,
        unsafe_allow_html=True,
    )
    if user:
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Email", value=user.get("email", ""), disabled=True)
        with c2:
            st.text_input("Name", value=user.get("name", ""), disabled=True)
        if user.get("linkedin_connected"):
            st.success("LinkedIn is connected.")
        else:
            st.warning("LinkedIn is not connected yet.")

    st.divider()

    # ── Profile Section ──────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-weight:600; font-size:1rem; color:#E8E8ED; margin-bottom:.5rem; display:flex; align-items:center; gap:6px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A66C2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pencil"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
            Your Profile
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    c1, c2 = st.columns(2)
    with c1:
        new_title = st.text_input(
            "Job title",
            value=profile_data["title"],
            key="user_title"
        )
    with c2:
        new_company = st.text_input(
            "Company",
            value=profile_data["company"],
            key="user_company"
        )
    new_interests = st.text_area(
        "Interests",
        value=profile_data["interests"],
        key="user_interests",
        height=100,
    )
    new_skills = st.text_area(
        "Skills",
        value=profile_data["skills"],
        key="user_skills",
        height=100,
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

    # ── LinkedIn Section ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-weight:600; font-size:1rem; color:#E8E8ED; margin-bottom:.5rem; display:flex; align-items:center; gap:6px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A66C2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-link"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            LinkedIn Connection
        </div>
        """,
        unsafe_allow_html=True,
    )
    if user.get("linkedin_connected"):
        st.success("Your LinkedIn account is linked.")
        if st.button("Reconnect LinkedIn", use_container_width=True):
            import asyncio

            with st.spinner("Opening LinkedIn..."):
                ok, message = asyncio.run(connect_user_linkedin(user["id"]))
            if ok:
                st.success("LinkedIn reconnected.")
            else:
                st.error(message)
    else:
        st.warning("Connect LinkedIn from the onboarding screen to use the feed.")

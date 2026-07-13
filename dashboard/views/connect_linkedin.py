import asyncio

import streamlit as st

from services.auth_service import refresh_user
from services.user_linkedin_service import connect_user_linkedin


def render():
    user = st.session_state.get("user") or {}

    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 2rem 0 1rem;">
                <div style="
                    display:inline-block;
                    width:72px; height:72px;
                    border-radius:20px;
                    background: linear-gradient(135deg, #0A66C2 0%, #63B3ED 100%);
                    line-height:72px;
                    font-size:2rem;
                    margin-bottom:1rem;
                    box-shadow: 0 8px 32px rgba(10, 102, 194, .3);
                ">🔗</div>
                <h2 style="margin:0 0 .3rem; font-weight:700; color:#E8E8ED;">
                    Connect your LinkedIn
                </h2>
                <p style="color:#9D9DB7; font-size:0.9rem; margin:0;">
                    Hi <strong>{user.get('name', 'there')}</strong>, link your LinkedIn account to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info("We'll open LinkedIn in your browser. Sign in once and you're all set.")

        if st.button("🔗 Connect LinkedIn", type="primary", use_container_width=True):
            with st.spinner("Opening LinkedIn..."):
                ok, message = asyncio.run(connect_user_linkedin(user["id"]))
            if ok:
                updated = refresh_user(user["id"])
                if updated:
                    st.session_state["user"] = updated
                st.success("LinkedIn connected successfully!")
                # Add user_id to URL for session recovery on refresh
                st.query_params["user_id"] = user["id"]
                st.rerun()
            else:
                st.error(message)

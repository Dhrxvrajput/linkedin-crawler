import asyncio

import streamlit as st

from services.auth_service import refresh_user
from services.user_linkedin_service import connect_user_linkedin


def render():
    user = st.session_state.get("user") or {}

    st.title("Connect your LinkedIn")
    st.markdown(
        f"Hi **{user.get('name', 'there')}**, link your LinkedIn account to get started."
    )

    st.info("We'll open LinkedIn in your browser. Sign in once and you're all set.")

    if st.button("Connect LinkedIn", type="primary", use_container_width=True):
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

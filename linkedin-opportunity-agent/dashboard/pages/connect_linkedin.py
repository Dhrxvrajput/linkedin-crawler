import asyncio

import streamlit as st

from services.auth_service import refresh_user
from services.user_linkedin_service import connect_user_linkedin


def render():
    user = st.session_state.get("user") or {}

    st.title("Connect LinkedIn")
    st.markdown(
        f"Welcome, **{user.get('name', 'there')}**! "
        "Before using the dashboard, connect your LinkedIn account once."
    )

    st.info(
        "A Chrome window will open. Sign in to LinkedIn there. "
        "Your session is saved securely on this device for future crawls."
    )

    if st.button("Connect LinkedIn", type="primary", use_container_width=True):
        with st.spinner("Opening LinkedIn login in your browser..."):
            ok, message = asyncio.run(connect_user_linkedin(user["id"]))
        if ok:
            updated = refresh_user(user["id"])
            if updated:
                st.session_state["user"] = updated
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.divider()
    st.caption(
        "This step is required only once per account. "
        "Your app password is stored as a secure hash — we never save plain text passwords."
    )

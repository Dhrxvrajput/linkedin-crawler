import asyncio
import os
import sys
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

        # Detect if we are running in a headless/Streamlit Cloud environment
        is_headless = (
            os.environ.get("STREAMLIT_SERVER_HEADLESS") == "true" or
            (sys.platform.startswith("linux") and not os.environ.get("DISPLAY"))
        )

        if is_headless:
            tabs = st.tabs(["🔑 Cookie Authentication", "👤 Login Credentials"])
        else:
            tabs = st.tabs(["🔑 Cookie Authentication", "👤 Login Credentials", "🖥️ Headed Login"])

        # ── Tab 1: Cookie Auth ────────────────────────────────────────────────────────
        with tabs[0]:
            st.write("")
            st.markdown(
                "Paste your LinkedIn `li_at` cookie value. This is the **most secure** method "
                "and works 100% reliably in cloud/headless environments without needing your password or triggering captchas."
            )
            li_at_val = st.text_input(
                "li_at cookie value",
                type="password",
                placeholder="AQEDAT... (a long alphanumeric cookie)",
                help="Paste the value of the 'li_at' cookie from your logged-in LinkedIn session."
            )
            
            with st.expander("ℹ️ How to get your li_at cookie value"):
                st.markdown(
                    """
                    1. Open a web browser (e.g. Google Chrome) and go to **[linkedin.com](https://www.linkedin.com)**.
                    2. Check that you are logged in.
                    3. Right-click anywhere and choose **Inspect** (or press `Cmd+Option+I` / `F12`) to open Developer Tools.
                    4. Go to the **Application** tab (or **Storage** in Firefox).
                    5. In the left panel, expand **Cookies** and click on `https://www.linkedin.com`.
                    6. Find the cookie named **`li_at`** in the table.
                    7. Double-click and copy its **Value** (a long text string).
                    """
                )
            
            if st.button("🔗 Connect using Cookie", type="primary", use_container_width=True):
                if not li_at_val:
                    st.error("Please enter a valid li_at cookie value.")
                else:
                    with st.spinner("Connecting to LinkedIn using cookie..."):
                        ok, message = asyncio.run(connect_user_linkedin(user["id"], li_at=li_at_val))
                    if ok:
                        updated = refresh_user(user["id"])
                        if updated:
                            st.session_state["user"] = updated
                        st.success("LinkedIn connected successfully!")
                        st.query_params["user_id"] = user["id"]
                        st.rerun()
                    else:
                        st.error(message)

        # ── Tab 2: Credentials Auth ───────────────────────────────────────────────────
        with tabs[1]:
            st.write("")
            st.markdown(
                "Log in using your LinkedIn credentials. They will only be processed for launching the crawler and "
                "are NOT permanently saved to the dashboard database."
            )
            email_val = st.text_input(
                "LinkedIn Email / Username",
                placeholder="email@example.com"
            )
            password_val = st.text_input(
                "LinkedIn Password",
                type="password",
                placeholder="••••••••"
            )
            
            if st.button("🔗 Connect using Credentials", type="primary", use_container_width=True):
                if not email_val or not password_val:
                    st.error("Please fill in both Email and Password fields.")
                else:
                    with st.spinner("Logging into LinkedIn... This might take up to a minute..."):
                        ok, message = asyncio.run(connect_user_linkedin(user["id"], email=email_val, password=password_val))
                    if ok:
                        updated = refresh_user(user["id"])
                        if updated:
                            st.session_state["user"] = updated
                        st.success("LinkedIn connected successfully!")
                        st.query_params["user_id"] = user["id"]
                        st.rerun()
                    else:
                        st.error(message)

        # ── Tab 3: Headed Auth (Local Only) ───────────────────────────────────────────
        if not is_headless:
            with tabs[2]:
                st.write("")
                st.info(
                    "This option will open a visible Chromium window on your computer screen. "
                    "You will be able to log in manually, complete any captchas or 2FA checks directly, "
                    "and the app will securely capture the session."
                )
                if st.button("🖥️ Open browser and login manually", type="primary", use_container_width=True):
                    with st.spinner("Opening browser window... Please check your computer screen."):
                        ok, message = asyncio.run(connect_user_linkedin(user["id"]))
                    if ok:
                        updated = refresh_user(user["id"])
                        if updated:
                            st.session_state["user"] = updated
                        st.success("LinkedIn connected successfully!")
                        st.query_params["user_id"] = user["id"]
                        st.rerun()
                    else:
                        st.error(message)

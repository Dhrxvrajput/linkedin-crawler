import streamlit as st

from services.auth_service import login, signup


def render():
    st.title("LinkedIn Opportunity Agent")
    st.markdown("Sign in or create an account to access your dashboard.")

    st.info(
        "Passwords are stored as a **secure one-way hash** (PBKDF2-SHA256). "
        "We never save or can recover your plain text password."
    )

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
            if submitted:
                ok, message, user = login(email, password)
                if ok and user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Name (optional)")
            email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            password = st.text_input("Password", type="password", help="At least 6 characters")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if submitted:
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, message = signup(email, password, name)
                    if ok:
                        st.success(message)
                    else:
                        st.error(message)

    st.divider()
    st.caption(
        "After your first login, you'll be asked to connect LinkedIn before using the feed."
    )

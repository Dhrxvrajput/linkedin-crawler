import streamlit as st

from services.auth_service import login, signup


def render():
    st.title("Welcome back")
    st.markdown("Sign in to manage your LinkedIn feed and opportunities.")

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
                    st.success("Welcome back!")
                    # Add user_id to URL for session recovery on refresh
                    st.query_params["user_id"] = user.get("id")
                    
                    # Store user_id in local file for 'Remember Me'
                    try:
                        from config.settings import BASE_DIR
                        (BASE_DIR / "storage" / "last_session.txt").write_text(str(user.get("id")))
                    except Exception:
                        pass
                        
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

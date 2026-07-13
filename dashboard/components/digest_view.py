import streamlit as st


def render_digest(text: str, height: int = 420):
    """Render full digest in a fixed-height scrollable panel."""
    if not text:
        st.markdown(
            """
            <div style="
                text-align:center;
                padding: 3rem 1rem;
                color:#9D9DB7;
            ">
                <div style="font-size:2.5rem; margin-bottom:.8rem;">📋</div>
                <p style="font-size:.9rem;">No digest generated yet.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    with st.container(height=height, border=True):
        st.markdown(text)

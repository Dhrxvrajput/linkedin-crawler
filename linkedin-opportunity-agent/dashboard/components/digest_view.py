import streamlit as st


def render_digest(text: str, height: int = 420):
    """Render full digest in a fixed-height scrollable panel."""
    if not text:
        st.info("No digest generated yet.")
        return

    with st.container(height=height, border=True):
        st.markdown(text)

import streamlit as st


def render_opportunity_card(opp, on_status_change=None):
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"### {opp.title}")
            st.caption(f"by {opp.author_name or 'Unknown'}")
        with col2:
            score = opp.relevance_score
            color = "green" if score >= 0.7 else "orange" if score >= 0.4 else "red"
            st.markdown(f":{color}[**{score:.0%}**]")
        with col3:
            st.badge(opp.opportunity_type)

        st.write(opp.description)

        if opp.tags:
            st.write(" ".join(f"`{tag}`" for tag in opp.tags))

        if opp.action_items:
            st.markdown("**Suggested Actions:**")
            for action in opp.action_items:
                st.markdown(f"- {action}")

        action_cols = st.columns(4)
        with action_cols[0]:
            if opp.author_profile_url:
                st.link_button("Profile", opp.author_profile_url)
        with action_cols[1]:
            if on_status_change and st.button("Reviewed", key=f"review_{opp.id}"):
                on_status_change(opp.id, "reviewed")
        with action_cols[2]:
            if on_status_change and st.button("Actioned", key=f"action_{opp.id}"):
                on_status_change(opp.id, "actioned")
        with action_cols[3]:
            if on_status_change and st.button("Dismiss", key=f"dismiss_{opp.id}"):
                on_status_change(opp.id, "dismissed")

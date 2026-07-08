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

        # Show current status badge
        status = opp.status or "new"
        st.caption(f"Current Status: **{status.title()}**")

        action_cols = st.columns(4)
        with action_cols[0]:
            if opp.author_profile_url:
                st.link_button("Profile", opp.author_profile_url, use_container_width=True)
        
        with action_cols[1]:
            is_reviewed = status == "reviewed"
            if on_status_change and st.button(
                "Reviewed" if not is_reviewed else "✓ Reviewed",
                key=f"review_{opp.id}",
                type="primary" if is_reviewed else "secondary",
                use_container_width=True,
                disabled=is_reviewed
            ):
                on_status_change(opp.id, "reviewed")
        
        with action_cols[2]:
            is_actioned = status == "actioned"
            if on_status_change and st.button(
                "Actioned" if not is_actioned else "✓ Actioned",
                key=f"action_{opp.id}",
                type="primary" if is_actioned else "secondary",
                use_container_width=True,
                disabled=is_actioned
            ):
                on_status_change(opp.id, "actioned")
        
        with action_cols[3]:
            if on_status_change and st.button("Dismiss", key=f"dismiss_{opp.id}", use_container_width=True):
                on_status_change(opp.id, "dismissed")

import streamlit as st

from dashboard.components.opportunity_card import render_opportunity_card
from services.opportunity_service import OpportunityService


def render():
    st.title("Opportunities")

    opp_service = OpportunityService()

    header_col, refresh_col = st.columns([4, 1])
    with refresh_col:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["new", "reviewed", "actioned", "dismissed", "all"], index=0)
    with col2:
        type_filter = st.selectbox(
            "Type",
            ["all", "job", "collaboration", "investment", "partnership", "speaking", "hiring", "networking", "other"],
            index=0
        )
    with col3:
        min_score = st.slider("Min Relevance Score", 0.0, 1.0, 0.0, 0.05)

    # Use 'new' as initial view, 'all' shows everything except dismissed
    status = status_filter
    if status_filter == "all":
        status = None # get_all with None returns all, we will manual filter dismissed below
    
    opportunities = opp_service.get_all(limit=500, status=status)
    
    # If viewing all, hide dismissed by default to keep list clean
    if status_filter == "all":
        opportunities = [o for o in opportunities if o.status != "dismissed"]
    opportunities = [o for o in opportunities if o.relevance_score >= min_score]
    if type_filter != "all":
        opportunities = [o for o in opportunities if o.opportunity_type == type_filter]

    st.caption(f"{len(opportunities)} opportunities — scroll to browse")

    def on_status_change(opp_id, new_status):
        opp_service.update_status(opp_id, new_status)
        st.rerun()

    with st.container(height=700, border=True):
        if not opportunities:
            st.info("No opportunities yet. Run the agent from the Home page.")
        for opp in opportunities:
            render_opportunity_card(opp, on_status_change=on_status_change)

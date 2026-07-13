import streamlit as st

from dashboard.components.opportunity_card import render_opportunity_card
from services.opportunity_service import OpportunityService


def render():
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(99, 179, 237, 0.04) 100%);
            border: 1px solid rgba(14, 165, 233, 0.12);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.2rem;
        ">
            <h2 style="margin:0 0 .3rem; font-weight:700; color:#E8E8ED; display:flex; align-items:center; gap:8px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-target"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                Opportunities
            </h2>
            <p style="margin:0; color:#9D9DB7; font-size:.9rem;">
                Discover and manage opportunities surfaced from your LinkedIn feed.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        status = None  # get_all with None returns all, we will manual filter dismissed below

    opportunities = opp_service.get_all(limit=500, status=status)

    # If viewing all, hide dismissed by default to keep list clean
    if status_filter == "all":
        opportunities = [o for o in opportunities if o.status != "dismissed"]
    opportunities = [o for o in opportunities if o.relevance_score >= min_score]
    if type_filter != "all":
        opportunities = [o for o in opportunities if o.opportunity_type == type_filter]

    opp_len_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-target" style="color:#0A66C2;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>'
    st.markdown(f'<div style="font-size:0.8rem; color:#9D9DB7; display:flex; align-items:center; gap:6px; margin-bottom: 8px;">{opp_len_svg} {len(opportunities)} opportunities — scroll to browse</div>', unsafe_allow_html=True)

    def on_status_change(opp_id, new_status):
        opp_service.update_status(opp_id, new_status)
        st.rerun()

    with st.container(height=700, border=False):
        if not opportunities:
            st.info("No opportunities yet. Run the agent from the Home page.")
        for opp in opportunities:
            render_opportunity_card(opp, on_status_change=on_status_change)

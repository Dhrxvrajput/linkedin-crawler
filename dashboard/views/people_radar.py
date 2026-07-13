import streamlit as st

from dashboard.components.people_card import render_people_card
from services.relationship_service import RelationshipService


def render():
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(10, 102, 194, 0.08) 0%, rgba(99, 179, 237, 0.04) 100%);
            border: 1px solid rgba(10, 102, 194, 0.12);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.2rem;
        ">
            <h2 style="margin:0 0 .3rem; font-weight:700; color:#E8E8ED; display:flex; align-items:center; gap:8px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users-round"><path d="M18 21a8 8 0 0 0-16 0"/><circle cx="10" cy="8" r="5"/><path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"/></svg>
                People Radar
            </h2>
            <p style="margin:0; color:#9D9DB7; font-size:.9rem;">
                Track key people and relationships from your network.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rel_service = RelationshipService()

    c1, c2 = st.columns(2)
    with c1:
        min_score = st.slider("Min Relevance Score", 0.0, 1.0, 0.0, 0.05)
    with c2:
        relationship_filter = st.selectbox(
            "Relationship",
            ["all", "direct_connection", "second_degree", "mutual_interest", "industry_peer", "unknown"],
        )

    people = rel_service.get_all(limit=100, min_score=min_score)
    if relationship_filter != "all":
        people = [p for p in people if p.relationship_type == relationship_filter]

    people_radar_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users-round" style="color:#0A66C2;"><path d="M18 21a8 8 0 0 0-16 0"/><circle cx="10" cy="8" r="5"/><path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"/></svg>'
    st.markdown(f'<div style="font-size:0.8rem; color:#9D9DB7; display:flex; align-items:center; gap:6px; margin-bottom: 8px;">{people_radar_svg} Tracking {len(people)} people</div>', unsafe_allow_html=True)

    with st.container(height=650, border=True):
        if not people:
            st.info("No people tracked yet. Run the agent to discover key contacts.")
        for person in people:
            render_people_card(person)

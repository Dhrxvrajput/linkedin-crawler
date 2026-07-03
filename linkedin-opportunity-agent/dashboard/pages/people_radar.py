import streamlit as st

from dashboard.components.people_card import render_people_card
from services.relationship_service import RelationshipService


def render():
    st.title("People Radar")

    rel_service = RelationshipService()

    min_score = st.slider("Min Relevance Score", 0.0, 1.0, 0.0, 0.05)
    relationship_filter = st.selectbox(
        "Relationship",
        ["all", "direct_connection", "second_degree", "mutual_interest", "industry_peer", "unknown"],
    )

    people = rel_service.get_all(limit=100, min_score=min_score)
    if relationship_filter != "all":
        people = [p for p in people if p.relationship_type == relationship_filter]

    st.caption(f"Tracking {len(people)} people")

    for person in people:
        render_people_card(person)

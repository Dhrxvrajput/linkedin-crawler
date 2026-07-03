import streamlit as st


def render_people_card(person):
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{person.name}**")
            if person.title:
                st.caption(f"{person.title}" + (f" at {person.company}" if person.company else ""))
        with col2:
            st.metric("Relevance", f"{person.relevance_score:.0%}")

        st.caption(f"Relationship: {person.relationship_type.replace('_', ' ').title()}")

        if person.shared_interests:
            st.write("Shared interests: " + ", ".join(f"`{i}`" for i in person.shared_interests))

        if person.recent_activity:
            st.write(person.recent_activity[:200])

        if person.profile_url:
            st.link_button("View Profile", person.profile_url)

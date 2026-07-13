import streamlit as st
from textwrap import dedent

_REL_ICONS = {
    "direct_connection": '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-link" style="color:#0A66C2;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "second_degree": '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-git-branch" style="color:#38BDF8;"><line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>',
    "mutual_interest": '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-lightbulb" style="color:#FBBF24;"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1 .3 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',
    "industry_peer": '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-building-2" style="color:#A78BFA;"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>',
    "unknown": '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-help-circle" style="color:#9D9DB7;"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>',
}


def render_people_card(person):
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            name = person.name or "Unknown"
            initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
            title_line = person.title or ""
            if person.company:
                title_line += f" at {person.company}" if title_line else person.company
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:10px;">'
                f'<div style="width:38px; height:38px; border-radius:10px; background: linear-gradient(135deg, #0A66C2, #63B3ED); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem; color:white; flex-shrink:0;">{initials}</div>'
                f'<div>'
                f'<div style="font-weight:600; font-size:.88rem; color:#E8E8ED; line-height:1.2;">{name}</div>'
                f'<div style="font-size:.75rem; color:#9D9DB7; line-height:1.3;">{title_line[:90] + "…" if len(title_line) > 90 else title_line}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            score = person.relevance_score
            if score >= 0.7:
                color = "#4ADE80"
            elif score >= 0.4:
                color = "#FBBF24"
            else:
                color = "#F87171"
            st.markdown(
                dedent(f"""
                <div style="
                    text-align:center;
                    font-size:1.3rem;
                    font-weight:700;
                    color: {color};
                ">{score:.0%}</div>
                <div style="text-align:center; font-size:.65rem; color:#9D9DB7; text-transform:uppercase; letter-spacing:.3px;">
                    Relevance
                </div>
                """),
                unsafe_allow_html=True,
            )

        rel_type = person.relationship_type
        icon_svg = _REL_ICONS.get(rel_type, _REL_ICONS["unknown"])
        st.markdown(
            dedent(f"""
            <div style="font-size:0.75rem; color:#9D9DB7; display:flex; align-items:center; gap:6px; margin: 4px 0 8px;">
                {icon_svg}
                <span>{rel_type.replace('_', ' ').title()}</span>
            </div>
            """),
            unsafe_allow_html=True
        )

        if person.shared_interests:
            interests_html = " ".join(
                f'<span style="'
                f"display:inline-block;"
                f"background:rgba(99,179,237,.10);"
                f"border:1px solid rgba(99,179,237,.18);"
                f"border-radius:6px;"
                f"padding:2px 8px;"
                f"font-size:.72rem;"
                f"color:#63B3ED;"
                f"font-weight:500;"
                f"margin:2px 3px 2px 0;"
                f'">{i}</span>'
                for i in person.shared_interests
            )
            st.markdown(interests_html, unsafe_allow_html=True)

        if person.recent_activity:
            with st.expander("Recent activity"):
                st.write(person.recent_activity[:300])

        if person.profile_url:
            st.link_button("🔗 View Profile", person.profile_url)

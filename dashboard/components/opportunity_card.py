import streamlit as st
from textwrap import dedent

_TYPE_ICONS = {
    "job": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-briefcase" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "collaboration": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-handshake" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><path d="m11 17 2 2a1 1 0 0 0 1.4 0l4-4a1 1 0 0 0 0-1.4l-2.6-2.6a1 1 0 0 0-1.4 0l-2 2a1 1 0 0 0 0 1.4Z"/><path d="m18 10 1-1A2 2 0 0 0 16 6a2 2 0 0 0-3 3l.4.4"/><path d="M12 14c0-1.7-1.3-3-3-3a3 3 0 0 0-3 3c0 1.7 1.3 3 3 3a3 3 0 0 0 3-3Z"/><path d="M3 14H2a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-1"/></svg>',
    "investment": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-coins" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><circle cx="8" cy="8" r="6"/><circle cx="18" cy="18" r="4"/><path d="M12 18a6 6 0 0 0-6-6"/><path d="M14 8h.01"/><path d="M18 14h.01"/></svg>',
    "partnership": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-building-2" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>',
    "speaking": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-mic" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>',
    "hiring": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-user-plus" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg>',
    "networking": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-globe" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
    "other": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pin" style="vertical-align: -3px; margin-right: 6.5px; color: #0A66C2;"><line x1="12" x2="12" y1="17" y2="22"/><path d="M5 17h14v-1.76a2 2 0 0 0-.44-1.24l-2.78-3.5A2 2 0 0 1 15 9.26V5a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4.26a2 2 0 0 1-.78 1.24l-2.78 3.5a2 2 0 0 0-.44 1.24Z"/></svg>',
}


def render_opportunity_card(opp, on_status_change=None):
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            icon_svg = _TYPE_ICONS.get(opp.opportunity_type, _TYPE_ICONS["other"])
            st.markdown(
                dedent(f"""
                <div style="
                    font-size: 1.15rem;
                    font-weight: 700;
                    color: #E8E8ED;
                    line-height: 1.3;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                ">{icon_svg}<span>{opp.title}</span></div>
                <div style="
                    font-size: .78rem;
                    color: #9D9DB7;
                    margin-top: 2px;
                ">by {opp.author_name or 'Unknown'}</div>
                """),
                unsafe_allow_html=True,
            )
        with col2:
            score = opp.relevance_score
            if score >= 0.7:
                color, bg = "#4ADE80", "rgba(74,222,128,.12)"
            elif score >= 0.4:
                color, bg = "#FBBF24", "rgba(251,191,36,.12)"
            else:
                color, bg = "#F87171", "rgba(248,113,113,.12)"
            st.markdown(
                dedent(f"""
                <div style="
                    text-align:center;
                    background: {bg};
                    border: 1px solid {color}33;
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-size: 1.2rem;
                    font-weight: 700;
                    color: {color};
                ">{score:.0%}</div>
                """),
                unsafe_allow_html=True,
            )
        with col3:
            st.badge(opp.opportunity_type)

        st.markdown(
            f'<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius:10px; padding:16px 20px; margin: 8px 0; line-height:1.6; font-size:0.93rem; color:#E8E8ED; white-space:pre-line;">{opp.description}</div>',
            unsafe_allow_html=True
        )

        if opp.tags:
            tags_html = " ".join(
                f'<span style="'
                f"display:inline-block;"
                f"background:rgba(10,102,194,.10);"
                f"border:1px solid rgba(10,102,194,.15);"
                f"border-radius:6px;"
                f"padding:2px 8px;"
                f"font-size:.72rem;"
                f"color:#5da9ff;"
                f"font-weight:500;"
                f"margin:2px 3px 2px 0;"
                f'">{tag}</span>'
                for tag in opp.tags
            )
            st.markdown(tags_html, unsafe_allow_html=True)

        if opp.action_items:
            with st.expander("Suggested Actions"):
                for action in opp.action_items:
                    st.markdown(f"- {action}")

        # Show current status badge
        status = opp.status or "new"
        status_colors = {
            "new": "#63B3ED",
            "reviewed": "#FBBF24",
            "actioned": "#4ADE80",
            "dismissed": "#9D9DB7",
        }
        s_color = status_colors.get(status, "#9D9DB7")
        st.markdown(
            dedent(f"""
            <div style="
                display: inline-block;
                background: {s_color}18;
                border: 1px solid {s_color}33;
                border-radius: 8px;
                padding: 3px 10px;
                font-size: .72rem;
                color: {s_color};
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: .3px;
                margin: 4px 0;
            ">● {status.title()}</div>
            """),
            unsafe_allow_html=True,
        )

        action_cols = st.columns(4)
        with action_cols[0]:
            if opp.author_profile_url:
                st.link_button("Profile", opp.author_profile_url, use_container_width=True)

        with action_cols[1]:
            is_reviewed = status == "reviewed"
            if on_status_change and st.button(
                "Reviewed" if is_reviewed else "Review",
                key=f"review_{opp.id}",
                type="primary" if is_reviewed else "secondary",
                use_container_width=True,
                disabled=is_reviewed
            ):
                on_status_change(opp.id, "reviewed")

        with action_cols[2]:
            is_actioned = status == "actioned"
            if on_status_change and st.button(
                "Actioned" if is_actioned else "Action",
                key=f"action_{opp.id}",
                type="primary" if is_actioned else "secondary",
                use_container_width=True,
                disabled=is_actioned
            ):
                on_status_change(opp.id, "actioned")

        with action_cols[3]:
            if on_status_change and st.button("Dismiss", key=f"dismiss_{opp.id}", use_container_width=True):
                on_status_change(opp.id, "dismissed")

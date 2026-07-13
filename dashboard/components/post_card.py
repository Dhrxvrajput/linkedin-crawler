import streamlit as st
from textwrap import dedent

_STATUS_LABELS = {
    "pending": ("⏳", "Not started"),
    "comment_ready": ("💬", "Comment ready"),
    "completed": ("✅", "Done"),
    "failed": ("❌", "Could not complete"),
}


def render_post_card(post):
    with st.container(border=True):
        # ── Author header ────────────────────────────────────────────────────
        col1, col2 = st.columns([3, 1])
        with col1:
            name = post.get("author_name", "Unknown")
            title = post.get("author_title") or ""
            initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"  
            st.markdown(
                dedent(f"""
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="
                        width:40px; height:40px;
                        border-radius:12px;
                        background: linear-gradient(135deg, #0A66C2, #63B3ED);
                        display:flex; align-items:center; justify-content:center;
                        font-weight:700; font-size:0.8rem; color:white;
                        flex-shrink:0;
                    ">{initials}</div>
                    <div>
                        <div style="font-weight:600; font-size:.9rem; color:#E8E8ED; line-height:1.2;">
                            {name}
                        </div>
                        <div style="font-size:.75rem; color:#9D9DB7; line-height:1.3;">
                            {title[:80] + '…' if len(title) > 80 else title}
                        </div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )
        with col2:
            if post.get("domain"):
                st.markdown(
                    dedent(f"""
                    <div style="
                        display:inline-block;
                        background: rgba(10,102,194,.12);
                        border: 1px solid rgba(10,102,194,.18);
                        border-radius: 8px;
                        padding: 4px 10px;
                        font-size: .72rem;
                        color: #5da9ff;
                        font-weight: 500;
                        text-transform: uppercase;
                        letter-spacing: .3px;
                    ">{post['domain']}</div>
                    """),
                    unsafe_allow_html=True,
                )

        posted = post.get("posted_display") or "Time unknown"
        calendar_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-calendar" style="vertical-align: -2px; margin-right: 4px; color: #9D9DB7;"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg>'
        st.markdown(f'<div style="font-size:0.75rem; color:#9D9DB7; display:flex; align-items:center; gap:2px; margin-bottom: 8px;">{calendar_svg}{posted}</div>', unsafe_allow_html=True)

        status = post.get("engagement_status") or "pending"

        # ── AI Section ────────────────────────────────────────────────────────
        if post.get("engagement_comment") or post.get("summary"):
            st.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, rgba(10,102,194,.06) 0%, rgba(99,179,237,.04) 100%);
                    border: 1px solid rgba(10,102,194,.10);
                    border-radius: 12px;
                    padding: 12px 16px;
                    margin: 6px 0;
                ">
                    <div style="font-weight:600; font-size:.8rem; color:#5da9ff; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="m5 3 1 2.5L8.5 6 6 7 5 9.5 4 7 1.5 6 4 5 5 3Z"/><path d="m19 17 1 2.5 2.5.5-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1 1-2.5Z"/></svg>
                        AI Analysis
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if post.get("engagement_comment"):
                st.success(f"**Draft Comment:** {post['engagement_comment']}")
                icon, label = _STATUS_LABELS.get(status, ("", status.replace("_", " ").title()))
                st.caption(f"{icon} Status: {label}")

            if post.get("summary"):
                with st.expander("Summary"):
                    st.write(post["summary"])

        st.divider()
        st.markdown(
            '<div style="font-weight:600; font-size:0.95rem; color:#E8E8ED; margin: 12px 0 6px; display:flex; align-items:center; gap:6px;">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-file-text" style="color:#0A66C2;"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>'
            'Post Content'
            '</div>', 
            unsafe_allow_html=True
        )
        content = post.get("content", "")
        limit = 1200
        if len(content) > limit:
            # Find the last space before the limit to avoid breaking words
            split_idx = content.rfind(" ", 0, limit)
            if split_idx == -1:
                split_idx = limit

            st.markdown(
                f'<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius:10px; padding:16px 20px; margin: 8px 0; line-height:1.6; font-size:0.93rem; color:#E8E8ED; white-space:pre-line;">{content[:split_idx]}...</div>',
                unsafe_allow_html=True
            )
            with st.expander("Show more"):
                st.markdown(
                    f'<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius:10px; padding:16px 20px; margin: 8px 0; line-height:1.6; font-size:0.93rem; color:#E8E8ED; white-space:pre-line;">{content[split_idx:].strip()}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                f'<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius:10px; padding:16px 20px; margin: 8px 0; line-height:1.6; font-size:0.93rem; color:#E8E8ED; white-space:pre-line;">{content}</div>',
                unsafe_allow_html=True
            )

        # ── Metrics row ──────────────────────────────────────────────────────
        metrics_cols = st.columns([2, 1])
        with metrics_cols[0]:
            st.markdown(
                dedent(f"""
                <div style="display:flex; gap:12px; align-items:center; height:38px;">
                    <div style="display:flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:6px 12px; border-radius:8px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                        <span style="font-size:0.75rem; color:#9D9DB7; font-weight:500;">Reactions</span>
                        <span style="font-size:0.85rem; color:#E8E8ED; font-weight:700;">{post.get("reactions_count", 0)}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:6px 12px; border-radius:8px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-message-square"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        <span style="font-size:0.75rem; color:#9D9DB7; font-weight:500;">Comments</span>
                        <span style="font-size:0.85rem; color:#E8E8ED; font-weight:700;">{post.get("comments_count", 0)}</span>
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with metrics_cols[1]:
            if post.get("author_profile_url"):
                st.link_button("View Profile", post["author_profile_url"], use_container_width=True)

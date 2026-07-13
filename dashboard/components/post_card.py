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
        name = post.get("author_name", "Unknown")
        title = post.get("author_title") or ""
        initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
        posted = post.get("posted_display") or "Time unknown"
        status = post.get("engagement_status") or "pending"

        # Domain badge HTML
        domain_badge = ""
        if post.get("domain"):
            domain_badge = f"""
            <div style="
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
            """

        # Header section containing author info
        st.markdown(
            dedent(f"""
            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom: 8px;">
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
                        <div style="font-size:.75rem; color:#9D9DB7; line-height:1.3; margin-top:2px;">
                            {title[:80] + '…' if len(title) > 80 else title}
                        </div>
                    </div>
                </div>
                {domain_badge}
            </div>
            """),
            unsafe_allow_html=True,
        )

        # Scraped date/posted calendar row
        calendar_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-calendar" style="vertical-align: -2px; margin-right: 4px; color: #9D9DB7;"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg>'
        st.markdown(
            f'<div style="font-size:0.75rem; color:#9D9DB7; display:flex; align-items:center; gap:2px; margin-bottom: 8px;">{calendar_svg}{posted}</div>',
            unsafe_allow_html=True
        )

        # ── AI Analysis Block (Rendered together in one clean box to save padding) ──
        if post.get("engagement_comment") or post.get("summary"):
            icon, label = _STATUS_LABELS.get(status, ("", status.replace("_", " ").title()))
            
            comment_block = ""
            if post.get("engagement_comment"):
                comment_block = f"""
                <div style="font-size:0.85rem; color:#E8E8ED; margin-top:8px; line-height:1.45;">
                    <span style="color:#63B3ED; font-weight:600;">Draft Comment:</span> {post['engagement_comment']}
                </div>
                <div style="font-size:0.75rem; color:#9D9DB7; margin-top:6px; display:inline-flex; align-items:center; gap:4px;">
                    <span>{icon}</span> <span>Status:</span> <span style="color:#E8E8ED; font-weight:500;">{label}</span>
                </div>
                """

            summary_block = ""
            if post.get("summary"):
                summary_block = f"""
                <details style="margin-top: 10px; font-size:0.8rem; color:#9D9DB7; cursor:pointer;">
                    <summary style="font-weight:600; color:#5da9ff; outline:none; margin-bottom:4px; list-style:none;">
                        ▼ View Summary
                    </summary>
                    <div style="padding: 8px 12px; background:rgba(255,255,255,0.02); border-radius:8px; line-height:1.45; color:#E8E8ED; border: 1px solid rgba(255,255,255,0.03); margin-top: 4px;">
                        {post['summary']}
                    </div>
                </details>
                """

            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, rgba(10,102,194,.06) 0%, rgba(99,179,237,.04) 100%);
                    border: 1px solid rgba(10,102,194,.10);
                    border-radius: 12px;
                    padding: 12px 14px;
                    margin: 8px 0;
                ">
                    <div style="font-weight:600; font-size:.8rem; color:#5da9ff; display:flex; align-items:center; gap:6px; margin-bottom: 2px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="m5 3 1 2.5L8.5 6 6 7 5 9.5 4 7 1.5 6 4 5 5 3Z"/><path d="m19 17 1 2.5 2.5.5-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1 1-2.5Z"/></svg>
                        AI Analysis
                    </div>
                    {comment_block}
                    {summary_block}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Subtle separator
        st.markdown(
            "<hr style='border:none; height:1px; background:linear-gradient(90deg, rgba(10, 102, 194, 0.15), transparent); margin: 10px 0 !important;' />",
            unsafe_allow_html=True
        )

        # Content Header
        st.markdown(
            '<div style="font-weight:600; font-size:0.85rem; color:#E8E8ED; margin: 4px 0 6px; display:flex; align-items:center; gap:6px;">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-file-text" style="color:#0A66C2;"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>'
            'Post Content'
            '</div>',
            unsafe_allow_html=True
        )

        content = post.get("content", "")
        limit = 650
        if len(content) > limit:
            split_idx = content.rfind(" ", 0, limit)
            if split_idx == -1:
                split_idx = limit
            content_short = content[:split_idx]
            content_remaining = content[split_idx:].strip()

            st.markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.015);
                    border: 1px solid rgba(255,255,255,0.03);
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin: 6px 0;
                    line-height: 1.55;
                    font-size: 0.88rem;
                    color: #E8E8ED;
                ">
                    <span style="white-space:pre-line;">{content_short}</span>
                    <details style="margin-top: 6px; font-size: 0.88rem;">
                        <summary style="outline:none; color:#378FE9; font-weight:600; cursor:pointer; list-style:none;" onclick="this.style.display='none'">
                            ▼ Read more
                        </summary>
                        <div style="white-space:pre-line; margin-top:6px; border-top:1px dashed rgba(255,255,255,0.06); padding-top:6px;">{content_remaining}</div>
                    </details>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.015);
                    border: 1px solid rgba(255,255,255,0.03);
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin: 6px 0;
                    line-height: 1.55;
                    font-size: 0.88rem;
                    color: #E8E8ED;
                    white-space: pre-line;
                ">{content}</div>
                """,
                unsafe_allow_html=True
            )

        # ── Footer metrics & custom View Profile button ──
        reactions_count = post.get("reactions_count", 0)
        comments_count = post.get("comments_count", 0)
        profile_url = post.get("author_profile_url")

        profile_button_html = ""
        if profile_url:
            profile_button_html = f"""
            <a href="{profile_url}" target="_blank" style="
                display: inline-block;
                background: rgba(10, 102, 194, 0.1);
                border: 1px solid rgba(10, 102, 194, 0.2);
                color: #E8E8ED;
                text-decoration: none;
                font-size: 0.78rem;
                font-weight: 500;
                padding: 6px 14px;
                border-radius: 6px;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='rgba(10, 102, 194, 0.2)'; this.style.borderColor='#0C7BE7';"
               onmouseout="this.style.background='rgba(10, 102, 194, 0.1)'; this.style.borderColor='rgba(10, 102, 194, 0.2)';">
                View Profile
            </a>
            """

        metrics_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; gap:10px;">
            <div style="display:flex; gap:10px; align-items:center;">
                <div style="display:flex; align-items:center; gap:5px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:5px 10px; border-radius:6px; font-size:0.75rem;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                    <span style="color:#9D9DB7; font-weight:500;">Reactions</span>
                    <span style="color:#E8E8ED; font-weight:700;">{reactions_count}</span>
                </div>
                <div style="display:flex; align-items:center; gap:5px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:5px 10px; border-radius:6px; font-size:0.75rem;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-message-square"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    <span style="color:#9D9DB7; font-weight:500;">Comments</span>
                    <span style="color:#E8E8ED; font-weight:700;">{comments_count}</span>
                </div>
            </div>
            {profile_button_html}
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)

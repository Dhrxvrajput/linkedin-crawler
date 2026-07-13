import sys
import os
from pathlib import Path

# Ensure consistent Playwright browser cache location across headless/cloud user environments
if sys.platform != "darwin":
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/pw-browsers"

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force reload all custom project modules to flush sys.modules cache on Streamlit Cloud
for module_name in list(sys.modules.keys()):
    if any(module_name.startswith(p) for p in ["services", "linkedin", "utils", "database", "config", "schemas"]):
        sys.modules.pop(module_name, None)

from config.settings import BASE_DIR, get_settings
from database.db import setup_database

st.set_page_config(
    page_title="LinkedIn Opportunity Agent",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

setup_database()

# ── Programmatic Playwright Chromium Installation ─────────────────────────────
@st.cache_resource
def install_playwright_browsers():
    import os
    import sys
    # Detect headless environments directly without imports
    is_headless = (
        os.environ.get("STREAMLIT_SERVER_HEADLESS") == "true" or
        (sys.platform.startswith("linux") and not os.environ.get("DISPLAY"))
    )
    if is_headless:
        import subprocess
        try:
            # Install chromium binary and dependencies on Streamlit Cloud using active interpreter path to prevent FileNotFoundError
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        except Exception as e:
            st.warning(f"Programmatic Playwright installation warning: {e}")

install_playwright_browsers()

settings = get_settings()

# ── Premium Global CSS ────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ─── CSS Variables ───────────────────────────── */
    :root {
        --bg-color: #0B0E14;
        --txt-color: #E8E8ED;
        --card-bg: #161922;
        --card-border: rgba(10, 102, 194, .12);
        --card-hover-border: #378FE9;
        --text-muted: #9D9DB7;
        --hero-bg: linear-gradient(135deg, rgba(10, 102, 194, 0.08) 0%, rgba(99, 179, 237, 0.04) 100%);
        --hero-border: rgba(10, 102, 194, 0.12);
        --tab-list-bg: rgba(26, 29, 41, .6);
        --tab-bg: transparent;
        --tab-selected-bg: rgba(10, 102, 194, .18);
        --tab-selected-color: #E8E8ED;
        --tab-color: #9D9DB7;
        --tab-hover-color: #E8E8ED;
        --tab-hover-bg: rgba(10, 102, 194, .08);
        --tab-highlight: #0A66C2;
        --sidebar-bg: linear-gradient(180deg, #12141D 0%, #1A1D29 100%);
        --nav-color: #9D9DB7;
        --nav-hover-color: #E8E8ED;
        --nav-active-color: #E8E8ED;
        --nav-hover-bg: rgba(10, 102, 194, 0.08);
        --nav-active-bg: rgba(10, 102, 194, 0.18);
        --subcard-bg: linear-gradient(135deg, rgba(10,102,194,.06) 0%, rgba(99,179,237,.04) 100%);
        --subcard-border: rgba(10,102,194,.10);
        --input-bg: rgba(26, 29, 41, .55);
        --input-border: rgba(10, 102, 194, .15);
        --expander-bg: rgba(26, 29, 41, .4);
        --metric-blue-bg: rgba(10, 102, 194, 0.12);
        --metric-target-bg: rgba(56, 189, 248, 0.12);
        --metric-yellow-bg: rgba(251, 191, 36, 0.12);
        --metric-purple-bg: rgba(167, 139, 250, 0.12);
        --metric-green-bg: rgba(52, 211, 153, 0.12);
    }

    /* ─── Global Overrides ─────────────────────────── */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-color) !important;
    }
    .main p, .main span, .main label, .main li, .main a {
        color: var(--txt-color);
    }
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: var(--txt-color) !important;
    }
    
    /* Overrides for hardcoded colors in custom HTML blocks */
    .main [style*="color:#E8E8ED"], .main [style*="color: #E8E8ED"], .main [style*="color:rgb(232, 232, 237)"] {
        color: var(--txt-color) !important;
    }
    .main [style*="color:#9D9DB7"], .main [style*="color: #9D9DB7"], .main [style*="color:rgb(157, 157, 183)"] {
        color: var(--text-muted) !important;
    }
    .main [style*="background: #1e1e24"], .main [style*="background:#1e1e24"] {
        background: var(--card-bg) !important;
    }
    
    /* Hero Headers dynamically themes */
    .main [style*="background: linear-gradient(135deg, rgba(10, 102, 194, 0.08)"],
    .main [style*="background: linear-gradient(135deg, rgba(108, 99, 255, 0.12)"],
    .main [style*="background: linear-gradient(135deg, rgba(108,99,255,.12) 0%, rgba(99,179,237,.08) 100%)"],
    .main [style*="background: linear-gradient(135deg, rgba(10, 102, 194, 0.08) 0%, rgba(99, 179, 237, 0.04) 100%)"],
    .main [style*="background: linear-gradient(135deg, rgba(108,99,255,.12)"] {
        background: var(--hero-bg) !important;
        border: 1px solid var(--hero-border) !important;
    }

    /* ─── Base ─────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        padding-left: 3.5rem !important;
        padding-right: 3.5rem !important;
        max-width: 94% !important;
    }

    /* ─── Sidebar ──────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--sidebar-bg);
        border-right: 1px solid rgba(10, 102, 194, .12);
    }
    section[data-testid="stSidebar"] .stRadio label {
        border-radius: 10px;
        padding: 6px 14px !important;
        transition: all .25s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(10, 102, 194, .10);
    }
    section[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
        background: rgba(10, 102, 194, .18) !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        border-radius: 10px;
        font-weight: 500;
        transition: all .3s ease;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(10, 102, 194, .25);
    }

    /* ─── Cards / Containers ───────────────────────── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--card-border) !important;
        border-radius: 12px !important;
        background: var(--card-bg) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 16px 20px !important;
        transition: border-color .3s ease, box-shadow .3s ease;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--card-hover-border) !important;
        box-shadow: 0 4px 20px rgba(10, 102, 194, .06);
    }
    /* Inner nested container cards spacing optimization */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 12px 14px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
    }

    /* ─── Metrics ──────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: var(--subcard-bg) !important;
        border: 1px solid var(--subcard-border) !important;
        border-radius: 12px;
        padding: 14px 18px;
        transition: transform .25s ease, box-shadow .25s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(10, 102, 194, .15);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        font-size: 1.6rem !important;
        background: linear-gradient(135deg, #0A66C2 0%, #63B3ED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ─── Tabs ─────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--tab-list-bg);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(10, 102, 194, .08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 8px 20px !important;
        font-weight: 500;
        transition: all .25s ease;
        color: var(--tab-color);
        background: var(--tab-bg);
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--tab-hover-color);
        background: var(--tab-hover-bg);
    }
    .stTabs [aria-selected="true"] {
        background: var(--tab-selected-bg) !important;
        color: var(--tab-selected-color) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--tab-highlight) !important;
        border-radius: 10px;
    }

    /* ─── Buttons ──────────────────────────────────── */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 8px 20px !important;
        transition: all .3s cubic-bezier(.4,0,.2,1) !important;
        border: 1px solid rgba(10, 102, 194, .2) !important;
        background: var(--card-bg) !important;
        color: var(--txt-color) !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(10, 102, 194, .2) !important;
        border-color: #0A66C2 !important;
    }
    .stButton button[kind="primary"],
    .stButton button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #0A66C2 0%, #004182 100%) !important;
        border: none !important;
        color: white !important;
    }
    .stButton button[kind="primary"]:hover,
    .stButton button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #378FE9 0%, #0A66C2 100%) !important;
        box-shadow: 0 6px 24px rgba(10, 102, 194, .35) !important;
    }

    /* ─── Inputs ───────────────────────────────────── */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px !important;
        border-color: var(--input-border) !important;
        background-color: var(--input-bg) !important;
        color: var(--txt-color) !important;
        transition: border-color .3s ease, box-shadow .3s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0A66C2 !important;
        box-shadow: 0 0 0 2px rgba(10, 102, 194, .2) !important;
    }

    /* ─── Expanders ────────────────────────────────── */
    details[data-testid="stExpander"] {
        border: 1px solid rgba(10, 102, 194, .10) !important;
        border-radius: 12px !important;
        background: var(--expander-bg) !important;
        transition: border-color .3s ease;
    }
    details[data-testid="stExpander"]:hover {
        border-color: rgba(10, 102, 194, .25) !important;
    }

    /* ─── Divider ──────────────────────────────────── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(10, 102, 194, .25), transparent) !important;
        margin: 1.2rem 0 !important;
    }

    /* ─── Alerts / Info boxes ──────────────────────── */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(10, 102, 194, .12) !important;
        background-color: var(--card-bg) !important;
    }

    /* ─── Link buttons ─────────────────────────────── */
    .stLinkButton a {
        border-radius: 10px !important;
        transition: all .3s ease !important;
        background: var(--card-bg) !important;
        color: var(--txt-color) !important;
        border: 1px solid rgba(10, 102, 194, .2) !important;
    }
    .stLinkButton a:hover {
        transform: translateY(-1px) !important;
        border-color: #0A66C2 !important;
    }

    /* ─── Badges ───────────────────────────────────── */
    [data-testid="stBadge"] span {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* ─── Multiselect ──────────────────────────────── */
    .stMultiSelect div[data-baseweb="select"] {
        border-radius: 10px !important;
        border-color: var(--input-border) !important;
        background-color: var(--input-bg) !important;
    }

    /* ─── Slider ───────────────────────────────────── */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: #0A66C2 !important;
        border-color: #0A66C2 !important;
    }

    /* ─── Smooth page transitions ──────────────────── */
    .main .block-container {
        animation: fadeUp .4s ease-out;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ─── Scrollbar ────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(10, 102, 194, .25);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(10, 102, 194, .45);
    }

    /* ─── Custom Sidebar Nav & Transitions ────────── */
    .custom-nav-container {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 0.5rem 0;
    }
    .custom-nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        border-radius: 12px;
        color: var(--nav-color) !important;
        text-decoration: none !important;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
    }
    .custom-nav-item svg {
        color: var(--nav-color);
        stroke: currentColor;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .custom-nav-item:hover {
        color: var(--nav-hover-color) !important;
        background: var(--nav-hover-bg) !important;
        border-color: rgba(10, 102, 194, 0.15) !important;
        transform: translateX(4px);
    }
    .custom-nav-item:hover svg {
        color: #0A66C2;
        transform: scale(1.08) rotate(3deg);
    }
    .custom-nav-item.active {
        color: var(--nav-active-color) !important;
        background: var(--nav-active-bg) !important;
        border-color: rgba(10, 102, 194, 0.3) !important;
    }
    .custom-nav-item.active svg {
        color: #378FE9;
    }

    .custom-logout-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        border-radius: 12px;
        color: #F87171 !important;
        text-decoration: none !important;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        background: rgba(248, 113, 113, 0.04);
        border: 1px solid rgba(248, 113, 113, 0.08);
        margin-top: 1rem;
    }
    .custom-logout-item svg {
        color: #F87171;
        stroke: currentColor;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .custom-logout-item:hover {
        color: #FF8F8F !important;
        background: rgba(248, 113, 113, 0.12) !important;
        border-color: rgba(248, 113, 113, 0.25) !important;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(248, 113, 113, 0.1);
    }
    .custom-logout-item:hover svg {
        transform: translateX(3px) scale(1.05);
    }

    .view-profile-btn:hover {
        background: rgba(10, 102, 194, 0.25) !important;
        border-color: #0C7BE7 !important;
        color: #E8E8ED !important;
        box-shadow: 0 2px 8px rgba(10, 102, 194, 0.15);
    }

    /* ─── Custom Tab SVG Icons ────────────────────── */
    .stTabs [data-baseweb="tab"]:nth-of-type(1)::before {
        content: "";
        display: inline-block;
        width: 16px;
        height: 16px;
        margin-right: 8px;
        background-size: contain;
        background-repeat: no-repeat;
        vertical-align: middle;
        transition: all 0.25s ease;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%239CA3AF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"]:nth-of-type(1)::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%230A66C2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
    }

    .stTabs [data-baseweb="tab"]:nth-of-type(2)::before {
        content: "";
        display: inline-block;
        width: 16px;
        height: 16px;
        margin-right: 8px;
        background-size: contain;
        background-repeat: no-repeat;
        vertical-align: middle;
        transition: all 0.25s ease;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%239CA3AF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 18h-5'/%3E%3Cpath d='M18 14h-8'/%3E%3Cpath d='M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-4 0v-9a2 2 0 0 1 2-2h2'/%3E%3Crect width='8' height='4' x='10' y='6' rx='1'/%3E%3C/svg%3E");
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"]:nth-of-type(2)::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%230A66C2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 18h-5'/%3E%3Cpath d='M18 14h-8'/%3E%3Cpath d='M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-4 0v-9a2 2 0 0 1 2-2h2'/%3E%3Crect width='8' height='4' x='10' y='6' rx='1'/%3E%3C/svg%3E");
    }

    .stTabs [data-baseweb="tab"]:nth-of-type(3)::before {
        content: "";
        display: inline-block;
        width: 16px;
        height: 16px;
        margin-right: 8px;
        background-size: contain;
        background-repeat: no-repeat;
        vertical-align: middle;
        transition: all 0.25s ease;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%239CA3AF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z'/%3E%3Cpath d='M6 6h10'/%3E%3Cpath d='M6 10h10'/%3E%3C/svg%3E");
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"]:nth-of-type(3)::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%230A66C2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z'/%3E%3Cpath d='M6 6h10'/%3E%3Cpath d='M6 10h10'/%3E%3C/svg%3E");
    }
    
    /* ─── Custom Metrics Row ──────────────────────── */
    .dashboard-metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 16px;
        margin-bottom: 2rem;
        width: 100%;
    }
    .dashboard-metric-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }
    .dashboard-metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(10, 102, 194, 0.3);
        box-shadow: 0 8px 30px rgba(10, 102, 194, 0.12);
        background: var(--card-bg);
    }
    .metric-icon-wrapper {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content:center;
        background: rgba(255, 255, 255, 0.04);
        flex-shrink: 0;
    }
    .metric-icon-wrapper svg {
        stroke-width: 2.2px;
    }
    .metric-icon-wrapper.blue {
        color: #0A66C2;
        background: var(--metric-blue-bg);
    }
    .metric-icon-wrapper.target {
        color: #38BDF8;
        background: var(--metric-target-bg);
    }
    .metric-icon-wrapper.yellow {
        color: #FBBF24;
        background: var(--metric-yellow-bg);
    }
    .metric-icon-wrapper.purple {
        color: #A78BFA;
        background: var(--metric-purple-bg);
    }
    .metric-icon-wrapper.green {
        color: #34D399;
        background: var(--metric-green-bg);
    }
    
    .metric-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .metric-title {
        font-size: 0.76rem;
        color: var(--text-muted);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-num {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--txt-color);
        line-height: 1.1;
    }

    @media (max-width: 1024px) {
        .dashboard-metrics-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    @media (max-width: 640px) {
        .dashboard-metrics-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

# Try to recover session from URL parameter or restore last user
session_file = BASE_DIR / "storage" / "last_session.txt"

if settings.auth_required and not st.session_state.get("authenticated"):
    query_params = st.query_params
    user_id_to_recover = query_params.get("user_id")

    # If no URL param, try the local 'Remember Me' file
    if not user_id_to_recover and session_file.exists():
        try:
            user_id_to_recover = session_file.read_text().strip()
        except Exception:
            pass

    if user_id_to_recover:
        from database.db import get_db
        from database.models import AppUser

        try:
            with get_db() as db_session:
                user = db_session.query(AppUser).filter(AppUser.id == user_id_to_recover).first()
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "linkedin_connected": user.linkedin_connected,
                    }
        except Exception:
            pass

if settings.auth_required and not st.session_state.get("authenticated"):
    from dashboard.views import login

    login.render()
    st.stop()

user = st.session_state.get("user")
if settings.auth_required and user and not user.get("linkedin_connected"):
    from dashboard.views import connect_linkedin

    connect_linkedin.render()
    st.stop()

# Handle custom HTML-based logout
if st.query_params.get("logout") == "true":
    st.session_state.clear()
    st.query_params.clear()
    if session_file.exists():
        try:
            session_file.unlink()
        except Exception:
            pass
    st.rerun()

# ── Navigation ────────────────────────────────────────────────────────────────
PAGES = {
    "Home": "dashboard.views.home",
    "Opportunities": "dashboard.views.opportunities",
    "People Radar": "dashboard.views.people_radar",
    "Research": "dashboard.views.research",
    "Settings": "dashboard.views.settings",
}

selection = st.query_params.get("page", "Home")
if selection not in PAGES:
    selection = "Home"

# Sidebar
st.sidebar.markdown(
    """
    <div style="
        text-align:center;
        padding: 1.2rem 0 .6rem;
    ">
        <div style="
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:56px; height:56px;
            border-radius:16px;
            background: linear-gradient(135deg, #0A66C2 0%, #63B3ED 100%);
            margin-bottom:.5rem;
            color: white;
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-link-2"><path d="M9 17H7A5 5 0 0 1 7 7h2"/><path d="M15 7h2a5 5 0 0 1 0 10h-2"/><line x1="8" x2="16" y1="12" y2="12"/></svg>
        </div>
        <h3 style="margin:0; font-size:1.1rem; font-weight:600; color:#E8E8ED;">
            LinkedIn Agent
        </h3>
    </div>
    """,
    unsafe_allow_html=True,
)

if user:
    name = user.get("name") or user.get("email", "User")
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "U"
    st.sidebar.markdown(
        f"""
        <div style="
            display:flex; align-items:center; gap:10px;
            background: rgba(10, 102, 194, .08);
            border: 1px solid rgba(10, 102, 194, .12);
            border-radius: 12px;
            padding: 10px 14px;
            margin-bottom: 1rem;
        ">
            <div style="
                width:36px; height:36px;
                border-radius:10px;
                background: linear-gradient(135deg, #0A66C2, #63B3ED);
                display:flex; align-items:center; justify-content:center;
                font-weight:700; font-size:0.85rem; color:white;
                flex-shrink:0;
            ">{initials}</div>
            <div>
                <div style="font-weight:600; font-size:0.85rem; color:#E8E8ED; line-height:1.2;">
                    {name}
                </div>
                <div style="font-size:0.7rem; color:#9D9DB7;">Online</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")

# Render custom HTML items with those exact Lucide SVGs and smooth transition effects
home_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-house"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>'

opp_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-briefcase-business"><path d="M12 12h.01"/><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><path d="M22 13a18.15 18.15 0 0 1-20 0"/><rect width="20" height="14" x="2" y="6" rx="2"/></svg>'

people_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users-round"><path d="M18 21a8 8 0 0 0-16 0"/><circle cx="10" cy="8" r="5"/><path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3"/></svg>'

research_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flask-conical"><path d="M10 2v7.586a2 2 0 0 1-.586 1.414l-5.69 5.69A2 2 0 0 0 5.138 20h13.724a2 2 0 0 0 1.414-3.414l-5.69-5.69A2 2 0 0 1 13.586 9.586V2"/><path d="M8 2h8"/><path d="M6 16h12"/></svg>'

settings_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-settings"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>'

logout_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-log-out"><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/></svg>'

nav_items = [
    ("Home", home_svg),
    ("Opportunities", opp_svg),
    ("People Radar", people_svg),
    ("Research", research_svg),
    ("Settings", settings_svg),
]

nav_html = '<div class="custom-nav-container">'
for label, svg in nav_items:
    active_class = "active" if label == selection else ""
    nav_html += f'<a href="/?page={label}" target="_self" class="custom-nav-item {active_class}">{svg}<span>{label}</span></a>'

if settings.auth_required:
    nav_html += f'<a href="/?logout=true" target="_self" class="custom-logout-item">{logout_svg}<span>Log out</span></a>'
nav_html += '</div>'

st.sidebar.markdown(nav_html, unsafe_allow_html=True)

st.sidebar.markdown("---")

from services.task_runner import task_registry

# Check active tasks
crawl_status_sb = task_registry.get_task_status("crawl_feed")
agent_status_sb = task_registry.get_task_status("run_agent")
any_running_sb = bool((crawl_status_sb and crawl_status_sb["status"] == "running") or (agent_status_sb and agent_status_sb["status"] == "running"))

if st.sidebar.button("Refresh from LinkedIn", use_container_width=True, disabled=any_running_sb):
    from app import crawl_feed
    user_id = user.get("id") if user else None
    task_registry.start_task("crawl_feed", crawl_feed, user_id=user_id)
    st.rerun()

# Display active tasks in the sidebar if on a page other than Home (which handles it in detail)
if any_running_sb:
    st.sidebar.markdown("---")
    st.sidebar.caption("⏳ Background Task Running...")
    if crawl_status_sb and crawl_status_sb["status"] == "running":
        st.sidebar.info(f"🔄 **Updating Feed:**\n`{crawl_status_sb['progress']}`")
    if agent_status_sb and agent_status_sb["status"] == "running":
        st.sidebar.info(f"🧠 **AI Analyzing:**\n`{agent_status_sb['progress']}`")
    
    # Auto-rerun page to update sidebar status
    st.sidebar.markdown(
        """
        <script>
        // Automatic reload script tag can be handled via streamlit rerun below
        </script>
        """,
        unsafe_allow_html=True
    )


# ── Render selected page ──────────────────────────────────────────────────────
module = __import__(PAGES[selection], fromlist=["render"])
module.render()

# Automatically refresh the app if background task is running, updating status
if any_running_sb:
    import time
    time.sleep(2)
    st.rerun()

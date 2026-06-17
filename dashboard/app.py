import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

_EST = ZoneInfo("America/New_York")

st.set_page_config(
    page_title="Jarvis — Trading Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

  :root {
    --bg-primary:   #060608;
    --bg-card:      #0c0c14;
    --bg-card-hover:#111120;
    --bg-border:    #1a1a2e;
    --bg-border-hi: #252548;
    --gold:         #f0b429;
    --gold-dim:     #a87a1a;
    --cyan:         #00d4ff;
    --cyan-dim:     #006d82;
    --green:        #00e676;
    --red:          #ff4444;
    --text-1:       #f0f0f8;
    --text-2:       #8888aa;
    --text-3:       #44445a;
    --mono:         'JetBrains Mono', 'Courier New', monospace;
  }

  html { font-size: 15px; }

  html, body, [data-testid="stApp"] {
    background-color: var(--bg-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-1) !important;
  }

  /* ── Subtle grid overlay ── */
  [data-testid="stApp"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
      linear-gradient(rgba(0,212,255,0.015) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,255,0.015) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  .main .block-container {
    padding: 1.5rem 2rem 3rem !important;
    max-width: none !important;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a14 0%, #060608 100%) !important;
    border-right: 1px solid var(--bg-border) !important;
  }
  [data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; bottom: 0; right: 0;
    width: 1px;
    background: linear-gradient(180deg, transparent, var(--gold-dim), transparent);
    opacity: 0.4;
  }
  [data-testid="stSidebar"] .block-container { padding-top: 1.5rem !important; }

  /* ── Nav radio ── */
  .stRadio > div { gap: 0 !important; }
  .stRadio label {
    padding: 0.55rem 0.9rem !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    color: var(--text-2) !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.15s ease !important;
    border: 1px solid transparent !important;
  }
  .stRadio label:hover {
    color: var(--text-1) !important;
    background: var(--bg-card) !important;
    border-color: var(--bg-border) !important;
  }
  div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
    background: rgba(240,180,41,0.06) !important;
    border-color: rgba(240,180,41,0.2) !important;
    color: var(--gold) !important;
  }

  /* ── Metric containers ── */
  div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    transition: border-color 0.2s ease !important;
  }
  div[data-testid="metric-container"]:hover {
    border-color: var(--gold-dim) !important;
    box-shadow: 0 0 16px rgba(240,180,41,0.07) !important;
  }

  /* ── Headings ── */
  h1, h2 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-1) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
  }
  h3, h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-2) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.6rem !important;
  }

  hr {
    border: none !important;
    border-top: 1px solid var(--bg-border) !important;
    margin: 1rem 0 !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    background: transparent !important;
    border: 1px solid var(--bg-border-hi) !important;
    color: var(--text-2) !important;
    border-radius: 6px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s ease !important;
  }
  .stButton > button:hover {
    border-color: var(--gold) !important;
    color: var(--gold) !important;
    background: rgba(240,180,41,0.05) !important;
  }
  .stButton > button[kind="primary"] {
    background: rgba(240,180,41,0.1) !important;
    border-color: var(--gold) !important;
    color: var(--gold) !important;
  }

  /* ── Inputs ── */
  .stTextInput > div > div > input,
  .stNumberInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border-hi) !important;
    border-radius: 6px !important;
    color: var(--text-1) !important;
    font-family: var(--mono) !important;
    font-size: 0.92rem !important;
  }
  .stTextInput > div > div > input:focus,
  .stNumberInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(240,180,41,0.12) !important;
  }

  /* ── Selectbox ── */
  .stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border-hi) !important;
    border-radius: 6px !important;
    color: var(--text-1) !important;
    font-size: 0.92rem !important;
  }

  /* ── Expander ── */
  .streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border) !important;
    border-radius: 8px !important;
    color: var(--text-2) !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
  }
  .streamlit-expanderContent {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
  }

  /* ── Progress bar ── */
  .stProgress > div > div {
    background: var(--bg-border) !important;
    border-radius: 999px !important;
    height: 4px !important;
  }
  .stProgress > div > div > div {
    background: linear-gradient(90deg, var(--gold-dim), var(--gold)) !important;
    border-radius: 999px !important;
  }

  /* ── Alerts ── */
  .stAlert {
    border-radius: 8px !important;
    border-left: 3px solid !important;
    font-size: 0.92rem !important;
  }

  /* ── Chat ── */
  .stChatMessage {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border) !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
  }
  .stChatInputContainer {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border-hi) !important;
    border-radius: 10px !important;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg-primary); }
  ::-webkit-scrollbar-thumb { background: var(--bg-border-hi); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--gold-dim); }

  .js-plotly-plot .plotly .bg { fill: transparent !important; }

  /* ── Checkbox ── */
  .stCheckbox label { color: var(--text-2) !important; font-size: 0.92rem !important; }

  /* ── Form container ── */
  [data-testid="stForm"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border) !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
  }

  /* ── Date input ── */
  .stDateInput > div > div > input {
    background: var(--bg-card) !important;
    border: 1px solid var(--bg-border-hi) !important;
    color: var(--text-1) !important;
    border-radius: 6px !important;
    font-size: 0.92rem !important;
  }

  /* ── Slider ── */
  .stSlider > div > div > div { background: var(--bg-border) !important; }
  .stSlider > div > div > div > div { background: var(--gold) !important; }

  /* ── Status glow dot ── */
  .jarvis-live {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--green);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--green), 0 0 16px var(--green);
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px var(--green), 0 0 16px var(--green); }
    50%       { opacity: 0.5; box-shadow: 0 0 3px var(--green); }
  }

  /* ── Scanlines ── */
  [data-testid="stApp"]::after {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 3px,
      rgba(0,0,0,0.03) 3px,
      rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 1;
  }

  /* ── Plotly tooltips ── */
  .plotly .hoverlayer .hovertext { font-family: var(--mono) !important; }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: var(--bg-primary) !important;
    border-bottom: 1px solid var(--bg-border) !important;
    gap: 0 !important;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--text-3) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.15s !important;
    background: transparent !important;
  }
  .stTabs [aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom-color: var(--gold) !important;
    background: rgba(240,180,41,0.04) !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: var(--text-2) !important;
    background: var(--bg-card) !important;
  }

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--bg-border-hi) !important;
    border-radius: 10px !important;
  }
  [data-testid="stFileUploader"]:hover { border-color: var(--gold-dim) !important; }

  /* ── Mobile ── */
  @media (max-width: 640px) {
    .main .block-container { padding: 0.8rem 0.6rem 2rem !important; }
    .stMetric { font-size: 0.85rem !important; }
  }
</style>
""", unsafe_allow_html=True)

from utils.airtable_client import get_daily_summaries
from components.overview import render_overview
from components.trade_log import render_trade_log
from components.performance import render_performance
from components.build_tracker import render_build_tracker
from components.ai_advisor import render_ai_advisor
from components.accounts import render_accounts
from components.markets import render_markets
from components.settings import render_settings

try:
    from utils.market_client import get_session_info
    _HAS_MARKET_CLIENT = True
except Exception:
    _HAS_MARKET_CLIENT = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    _now_sb = datetime.now(_EST)
    _sb_h12 = _now_sb.hour % 12 or 12
    _sb_pm  = "AM" if _now_sb.hour < 12 else "PM"
    st.markdown(
        f"<div style='padding:0.2rem 0 1rem'>"
        f"<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.25rem'>"
        f"<span style='font-size:1.3rem;filter:drop-shadow(0 0 6px #f0b429)'>⚡</span>"
        f"<span style='color:#f0f0f8;font-size:1.2rem;font-weight:700;"
        f"letter-spacing:0.05em;text-shadow:0 0 12px rgba(240,180,41,0.3)'>JARVIS</span>"
        f"</div>"
        f"<div style='color:#6666aa;font-size:0.72rem;letter-spacing:0.18em;"
        f"text-transform:uppercase;margin-bottom:0.5rem'>Trading Intelligence</div>"
        f"<div style='display:flex;align-items:baseline;gap:0.4rem;margin-bottom:0.5rem'>"
        f"<span style='color:#f0f0f8;font-size:1.25rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace;letter-spacing:0.02em'>"
        f"{_sb_h12}:{_now_sb.minute:02d}</span>"
        f"<span style='color:#f0b429;font-size:0.78rem;font-weight:700'>{_sb_pm}</span>"
        f"<span style='color:#f0b429;font-size:0.65rem;font-weight:700;letter-spacing:0.1em'>EST</span>"
        f"<span style='color:#555577;font-size:0.7rem'>{_now_sb.strftime('%a %b %d')}</span>"
        f"</div>"
        f"<div style='height:1px;background:linear-gradient(90deg,#f0b42944,transparent)'></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # Session badge
    try:
        if not _HAS_MARKET_CLIENT:
            raise ImportError
        sess      = get_session_info()
        sess_col  = sess["color"]
        sess_name = sess["session"]
        rem       = sess["remaining_min"]
        rem_h, rem_m = rem // 60, rem % 60
        sess_status = f"{'closes' if sess['active'] else 'opens'} {rem_h}h {rem_m}m"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.6rem;"
            f"background:#0a0a18;border:1px solid #1a1a2e;border-radius:8px;padding:0.5rem 0.7rem'>"
            f"<div style='width:8px;height:8px;border-radius:50%;background:{sess_col};"
            f"box-shadow:0 0 6px {sess_col}88;flex-shrink:0'></div>"
            f"<div><div style='color:{sess_col};font-size:0.82rem;font-weight:700'>{sess_name}</div>"
            f"<div style='color:#6666aa;font-size:0.72rem'>{sess_status}</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    except Exception:
        pass

    _pages = ["Overview", "Markets", "Accounts", "Analytics", "Build Tracker", "AI Advisor", "Settings"]
    _qp    = st.query_params.get("page", "Overview")
    _idx   = _pages.index(_qp) if _qp in _pages else 0

    page = st.radio(
        "nav",
        _pages,
        index=_idx,
        label_visibility="collapsed",
    )
    if st.query_params.get("page") != page:
        st.query_params["page"] = page

    st.divider()

    # Today's summary
    summaries = get_daily_summaries(1)
    if summaries:
        s   = summaries[0]
        pnl = s.get("pnl", 0) or 0
        wr  = s.get("win_rate", 0) or 0
        ddl_hit  = s.get("ddl_hit", False)
        closed_ok = s.get("closed_at_ddl", False)
        pnl_color = "#00e676" if pnl >= 0 else "#ff4444"
        st.markdown(
            f"<div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:8px;"
            f"padding:0.8rem;margin-bottom:0.8rem'>"
            f"<div style='color:#6666aa;font-size:0.8rem;text-transform:uppercase;"
            f"letter-spacing:0.1em;margin-bottom:0.4rem'>Today</div>"
            f"<div style='color:{pnl_color};font-size:1.3rem;font-weight:700;"
            f"font-family:JetBrains Mono,monospace'>{'+' if pnl >= 0 else ''}${pnl:,.2f}</div>"
            f"<div style='color:#8888aa;font-size:0.85rem;margin-top:0.2rem'>"
            f"{wr:.0f}% WR · {s.get('wins',0)}W {s.get('losses',0)}L</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if ddl_hit and not closed_ok:
            st.error("🚫 DDL HIT — STOP NOW")
        elif ddl_hit and closed_ok:
            st.success("✅ DDL closed correctly")
    else:
        st.markdown("<div style='color:#6666aa;font-size:0.85rem'>No data logged yet</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<div style='color:#6666aa;font-size:0.78rem;letter-spacing:0.05em'>Jarvis v1.0 · June 2026</div>", unsafe_allow_html=True)

# ── Page router ───────────────────────────────────────────────────────────────
if page == "Overview":
    render_overview()
elif page == "Markets":
    render_markets()
elif page == "Accounts":
    render_accounts()
elif page == "Analytics":
    st.markdown(
        "<div style='display:flex;align-items:baseline;gap:0.8rem;margin-bottom:1.2rem'>"
        "<span style='color:#f0f0f8;font-size:1.4rem;font-weight:700;letter-spacing:-0.02em'>Analytics</span>"
        "<span style='color:#252548;font-size:0.82rem;letter-spacing:0.1em;text-transform:uppercase'>performance</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    atab_log, atab_perf = st.tabs(["📋  Trade Log", "📊  Performance"])
    with atab_log:
        render_trade_log()
    with atab_perf:
        render_performance()
elif page == "Build Tracker":
    render_build_tracker()
elif page == "AI Advisor":
    render_ai_advisor()
elif page == "Settings":
    render_settings()

"""
Markets tab — market status, session clock, kill zones, live prices, AI TDA, news, live charts.
"""
import os
import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "config" / "config.env")

_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EST = ZoneInfo("America/New_York")

# Kill zones (name, start_h, start_m, end_h, end_m, color)
KILL_ZONES = [
    ("London KZ",   2,  0,  5,  0, "#00d4ff"),
    ("NY KZ",       7,  0, 12,  0, "#00e676"),
    ("3PM Window", 15,  0, 16, 30, "#f0b429"),
]


def _section(label: str):
    st.markdown(
        f"<div style='color:#6666aa;font-size:0.62rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:0.14em;margin:1.4rem 0 0.6rem;padding-bottom:0.4rem;"
        f"border-bottom:1px solid #1a1a2e'>{label}</div>",
        unsafe_allow_html=True,
    )


def _render_market_banner():
    from utils.market_client import get_market_status
    status = get_market_status()
    is_open = status["open"]
    detail  = status["detail"]
    bg      = "#061a0e" if is_open else "#160608"
    border  = "#00e67633" if is_open else "#ff444433"
    dot_col = "#00e676" if is_open else "#ff4444"
    label   = "MARKET OPEN" if is_open else "MARKET CLOSED"
    anim    = "animation:pulse 2s infinite;" if is_open else ""

    st.markdown(
        f"<div style='background:{bg};border:1px solid {border};border-radius:10px;"
        f"padding:0.7rem 1rem;margin-bottom:0.8rem;display:flex;align-items:center;gap:0.75rem'>"
        f"<div style='width:8px;height:8px;border-radius:50%;background:{dot_col};"
        f"box-shadow:0 0 10px {dot_col};{anim}flex-shrink:0'></div>"
        f"<span style='color:{dot_col};font-size:0.78rem;font-weight:700;"
        f"letter-spacing:0.08em'>{label}</span>"
        f"<span style='color:#6666aa;font-size:0.78rem'>{detail}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_session_clock():
    from utils.market_client import get_session_info, SESSIONS
    info = get_session_info()
    now  = datetime.now(EST)

    session   = info["session"]
    color     = info["color"]
    remaining = info["remaining_min"]
    nxt       = info["next"]
    active    = info["active"]

    rem_h = remaining // 60
    rem_m = remaining % 60

    pulse_anim = "" if not active else "animation:pulse 2s infinite;"
    glow       = f"box-shadow:0 0 16px {color}44;" if active else ""

    session_pills = ""
    current_mins  = now.hour * 60 + now.minute
    for s_name, (sh, sm), (eh, em), s_color in SESSIONS:
        start = sh * 60 + sm
        end   = eh * 60 + em
        if s_name == "Asia":
            is_on = current_mins >= start or current_mins < end
        else:
            is_on = start <= current_mins < end
        alpha  = "ff" if is_on else "22"
        border = f"2px solid {s_color}" if is_on else f"1px solid {s_color}22"
        session_pills += (
            f"<div style='background:{s_color}{alpha};border:{border};border-radius:8px;"
            f"padding:0.4rem 0.9rem;text-align:center;min-width:90px'>"
            f"<div style='color:{'#060608' if is_on else s_color};font-size:0.65rem;"
            f"font-weight:700;letter-spacing:0.08em;text-transform:uppercase'>{s_name}</div>"
            f"<div style='color:{'#060608' if is_on else s_color+'88'};font-size:0.7rem;"
            f"font-family:JetBrains Mono,monospace'>"
            f"{'LIVE' if is_on else f'{sh:02d}:{sm:02d}–{eh:02d}:{em:02d}'} ET</div>"
            f"</div>"
        )

    st.markdown(
        f"<div style='background:#0c0c14;border:1px solid #1e1e38;border-radius:14px;"
        f"padding:1.2rem 1.5rem;margin-bottom:0.8rem'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"flex-wrap:wrap;gap:1rem'>"
        f"<div style='display:flex;align-items:center;gap:1rem'>"
        f"<div style='display:flex;align-items:center;gap:0.5rem'>"
        f"<div style='width:9px;height:9px;border-radius:50%;background:{color};{glow}{pulse_anim}'></div>"
        f"<span style='color:{color};font-size:1.05rem;font-weight:700;letter-spacing:0.04em'>{session}</span>"
        f"</div>"
        f"<div style='color:#f0f0f8;font-size:1.55rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace;letter-spacing:-0.02em'>"
        f"{now.strftime('%H:%M')}<span style='color:#6666aa;font-size:0.9rem'> ET</span></div>"
        f"<div style='color:#6666aa;font-size:0.8rem;line-height:1.4'>"
        f"{now.strftime('%A, %b %d')}<br>"
        f"<span style='color:#8888bb'>{('closes in ' if active else 'opens in ')}"
        f"{rem_h}h {rem_m}m &rarr; {nxt}</span>"
        f"</div></div>"
        f"<div style='display:flex;gap:0.5rem;flex-wrap:wrap'>{session_pills}</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _render_kill_zones():
    now = datetime.now(EST)
    cur = now.hour * 60 + now.minute

    pills = ""
    for kz_name, sh, sm, eh, em, color in KILL_ZONES:
        start = sh * 60 + sm
        end   = eh * 60 + em
        is_on = start <= cur < end

        if is_on:
            mins_left = end - cur
            badge     = f"{mins_left}m left"
            alpha     = "22"
            txt_col   = color
        else:
            if cur < start:
                mins_to = start - cur
            else:
                mins_to = (24 * 60 - cur) + start
            hh, mm = divmod(mins_to, 60)
            badge  = f"in {hh}h {mm}m" if hh else f"in {mm}m"
            alpha  = "0a"
            txt_col = "#6666aa"

        border   = f"2px solid {color}" if is_on else f"1px solid {color}33"
        time_str = f"{sh:02d}:{sm:02d}–{eh:02d}:{em:02d} ET"

        pills += (
            f"<div style='background:{color}{alpha};border:{border};border-radius:10px;"
            f"padding:0.65rem 1rem;flex:1;min-width:140px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem'>"
            f"<span style='color:{color};font-size:0.65rem;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.08em'>{kz_name}</span>"
            f"<span style='background:{color}22;color:{color};font-size:0.6rem;"
            f"font-weight:700;padding:1px 6px;border-radius:4px'>{'LIVE' if is_on else badge}</span>"
            f"</div>"
            f"<div style='color:{txt_col};font-size:0.72rem;"
            f"font-family:JetBrains Mono,monospace'>{time_str}</div>"
            f"</div>"
        )

    st.markdown(
        f"<div style='display:flex;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.4rem'>{pills}</div>",
        unsafe_allow_html=True,
    )


def _render_prices():
    from utils.market_client import get_prices

    with st.spinner(""):
        prices = get_prices()

    if not prices:
        st.markdown(
            "<div style='color:#6666aa;font-size:0.85rem;padding:1rem'>Price data unavailable. "
            "Install yfinance: <code>pip install yfinance</code></div>",
            unsafe_allow_html=True,
        )
        return

    cols = st.columns(4)
    for i, p in enumerate(prices):
        up      = p["change"] >= 0
        chg_col = "#00e676" if up else "#ff4444"
        arr     = "▲" if up else "▼"
        price   = p["price"]
        fmt     = f"${price:,.2f}" if price >= 10 else f"${price:.4f}"

        with cols[i % 4]:
            st.markdown(
                f"<div style='background:#0a0a18;border:1px solid #1a1a30;border-radius:12px;"
                f"padding:0.85rem 1rem;margin-bottom:0.7rem;border-left:3px solid {p['color']}'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start'>"
                f"<div>"
                f"<div style='color:#6666aa;font-size:0.6rem;text-transform:uppercase;"
                f"letter-spacing:0.1em'>{p['name']}</div>"
                f"<div style='color:#f0f0f8;font-size:1.2rem;font-weight:700;"
                f"font-family:JetBrains Mono,monospace;margin-top:0.1rem'>{fmt}</div>"
                f"</div>"
                f"<div style='background:{p['color']}11;border-radius:6px;padding:2px 7px;margin-top:2px'>"
                f"<span style='color:{p['color']};font-size:0.7rem;font-weight:700'>{p['code']}</span>"
                f"</div></div>"
                f"<div style='color:{chg_col};font-size:0.8rem;font-family:JetBrains Mono,monospace;"
                f"margin-top:0.35rem'>{arr} {'+' if up else ''}{p['change']:,.2f}  ({p['change_pct']:+.2f}%)</div>"
                f"<div style='color:#5555aa;font-size:0.65rem;margin-top:0.15rem'>"
                f"prev {p['prev_close']:,.2f}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _render_tda():
    from utils.market_client import get_prices, get_session_info, generate_tda

    if not _API_KEY:
        st.markdown(
            "<div style='background:#0d0d20;border:1px solid #1e1e38;border-radius:10px;padding:1rem;"
            "color:#6666aa;font-size:0.85rem'>Add ANTHROPIC_API_KEY to config/config.env to enable AI TDA</div>",
            unsafe_allow_html=True,
        )
        return

    session = get_session_info()["session"]

    col1, col2 = st.columns([1, 5])
    with col1:
        regen = st.button("↻ Refresh", key="tda_refresh", help="Regenerate TDA (uses API tokens)")

    if regen:
        generate_tda.clear()

    with st.spinner("Generating TDA from CLS methodology…"):
        tda = generate_tda(
            date_key     = str(__import__("datetime").date.today()),
            session_name = session,
            api_key      = _API_KEY,
        )

    if not tda:
        st.markdown("<div style='color:#6666aa'>No TDA generated yet.</div>", unsafe_allow_html=True)
        return

    sections = {
        "HTF BIAS":            ("#f0b429", "📊"),
        "KEY LEVELS":          ("#00d4ff", "🎯"),
        "SESSION EXPECTATION": ("#00e676", "🕐"),
        "CLS SETUP WATCH":     ("#a78bfa", "⚡"),
        "RISK NOTE":           ("#ff6b6b", "⚠"),
    }

    lines     = tda.split("\n")
    current_h = None
    buf       = []
    rendered  = []

    for line in lines:
        clean   = line.strip().replace("**", "")
        matched = None
        for key in sections:
            if key in clean.upper():
                matched = key
                break
        if matched:
            if current_h and buf:
                rendered.append((current_h, "\n".join(buf).strip()))
            current_h = matched
            buf = []
        elif current_h:
            if line.strip():
                buf.append(line)
        else:
            if line.strip():
                buf.append(line)

    if current_h and buf:
        rendered.append((current_h, "\n".join(buf).strip()))

    if not rendered:
        st.markdown(
            f"<div style='background:#0a0a18;border:1px solid #1a1a30;border-radius:10px;"
            f"padding:1rem;color:#c8c8e8;font-size:0.88rem;line-height:1.7;white-space:pre-wrap'>{tda}</div>",
            unsafe_allow_html=True,
        )
        return

    for heading, body in rendered:
        color, icon = sections.get(heading, ("#8888bb", "·"))
        is_risk  = heading == "RISK NOTE"
        border   = f"border-left:3px solid {color};" if is_risk else f"border-top:2px solid {color}22;"
        body_html = body.replace("\n", "<br>").replace(
            "- ", f"<span style='color:{color}'>▸</span> "
        )
        st.markdown(
            f"<div style='background:{'#120808' if is_risk else '#0a0a18'};"
            f"border:1px solid {'#ff6b6b44' if is_risk else '#1a1a30'};"
            f"{border}border-radius:10px;padding:0.85rem 1.1rem;margin-bottom:0.6rem'>"
            f"<div style='color:{color};font-size:0.65rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.12em;margin-bottom:0.5rem'>{icon} {heading}</div>"
            f"<div style='color:#d0d0f0;font-size:0.88rem;line-height:1.7'>{body_html}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    now = datetime.now(EST)
    st.markdown(
        f"<div style='color:#5555aa;font-size:0.65rem;margin-top:0.3rem'>"
        f"Generated {now.strftime('%b %d %H:%M ET')} · Haiku 4.5 · CLS methodology context</div>",
        unsafe_allow_html=True,
    )


def _render_news():
    from utils.market_client import get_news

    with st.spinner(""):
        headlines = get_news()

    if not headlines:
        st.markdown(
            "<div style='color:#6666aa;font-size:0.85rem'>News feed unavailable — check connection.</div>",
            unsafe_allow_html=True,
        )
        return

    source_colors = {
        "Reuters Markets": "#f0b429",
        "ForexLive":       "#00d4ff",
        "MarketWatch":     "#00e676",
        "Investing.com":   "#a78bfa",
    }

    news_html = ""
    for h in headlines:
        color = source_colors.get(h["source"], "#6666aa")
        title = h["title"][:120] + ("…" if len(h["title"]) > 120 else "")
        link  = h.get("link", "#")
        news_html += (
            f"<a href='{link}' target='_blank' style='text-decoration:none'>"
            f"<div style='padding:0.6rem 0;border-bottom:1px solid #13132a;"
            f"display:flex;align-items:flex-start;gap:0.6rem;cursor:pointer' "
            f"onmouseover=\"this.style.background='#0d0d20'\" "
            f"onmouseout=\"this.style.background='transparent'\">"
            f"<span style='background:{color}22;color:{color};font-size:0.58rem;font-weight:700;"
            f"padding:2px 6px;border-radius:4px;white-space:nowrap;margin-top:2px'>{h['source'][:8]}</span>"
            f"<span style='color:#c8c8e8;font-size:0.83rem;line-height:1.5'>{title}</span>"
            f"</div></a>"
        )

    st.markdown(
        f"<div style='background:#08080f;border:1px solid #1a1a30;border-radius:10px;"
        f"padding:0.4rem 0.8rem;max-height:480px;overflow-y:auto'>{news_html}</div>",
        unsafe_allow_html=True,
    )
    now = datetime.now(EST)
    st.markdown(
        f"<div style='color:#5555aa;font-size:0.65rem;margin-top:0.3rem'>"
        f"Refreshes every 15 min · {now.strftime('%H:%M ET')}</div>",
        unsafe_allow_html=True,
    )


def render_markets():
    st.markdown(
        "<div style='display:flex;align-items:baseline;gap:0.8rem;margin-bottom:1.2rem'>"
        "<span style='color:#f0f0f8;font-size:1.3rem;font-weight:700;letter-spacing:-0.02em'>Markets</span>"
        "<span style='color:#252548;font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase'>live intel</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Market open/closed banner
    _render_market_banner()

    tab_intel, tab_chart = st.tabs(["📊  Market Intel", "📈  Live Chart"])

    with tab_intel:
        # Session clock
        _section("SESSION CLOCK")
        _render_session_clock()

        # Kill zones
        _section("CLS KILL ZONES")
        _render_kill_zones()

        # Prices
        _section("LIVE PRICES")
        _render_prices()

        # TDA + News
        left, right = st.columns([3, 2])
        with left:
            _section("DAILY TOP DOWN ANALYSIS — CLS METHODOLOGY")
            _render_tda()
        with right:
            _section("MARKET NEWS")
            _render_news()

    with tab_chart:
        from components.charts import render_charts
        render_charts()

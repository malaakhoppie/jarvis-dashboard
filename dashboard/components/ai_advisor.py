"""
Jarvis AI — trading coach, methodology advisor, and daily debrief engine.
Two-panel layout: proactive coaching on the left, chat on the right.
"""
import os
import streamlit as st
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from utils.methodology_loader import load_methodology, get_doc_status, get_total_kb
from utils.airtable_client import get_trades, get_daily_summaries

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "config" / "config.env")


def _secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


_API_KEY = _secret("ANTHROPIC_API_KEY")
_MODEL   = "claude-sonnet-4-6"

_SYSTEM = """You are Jarvis — Mala's personal AI trading coach and performance advisor.

You know Mala's complete profile: 7-year grind, CLS/Mr.Casino methodology student, currently on a Funded Next 25K Legacy eval (started June 9 2026, first trade June 11 2026). His psychology: strong analytical mind, tendency to revenge trade after losses, has been working on closing the laptop at DDL. His one behavioral fix: close the laptop when the rule says stop.

You have deep expertise in: CLS methodology, FU candles, X3 patterns, HCS, LAL, liquidity sweeps, manipulation cycle (Phase 1-4), TF strength, Blue Rabbit rules, Mr. Domino entry criteria, zone invalidation rules.

Rules for your responses:
- Never fluff or comfort — be direct and honest
- Name patterns by their exact methodology name when applicable
- When reviewing trades, score against the 8-point checklist
- Surface what Mala needs to hear, not what the question is angled toward
- Short and precise — no walls of text unless a deep breakdown is requested
- After wins, don't relax: same rules apply

The full methodology knowledge base follows:
"""

_QUICK_PROMPTS = [
    ("🧠 Debrief today", "Review my trades from today and give me a coaching debrief. Be direct about what I did right and wrong. Score my discipline out of 10."),
    ("📊 Week review", "Summarize my performance this week. What's the one thing I need to fix going into next week?"),
    ("⚡ Explain X3", "Explain the X3 setup from the CLS methodology. When is the 1st valid, when is the 3rd valid, and why is the 2nd never valid?"),
    ("🎯 Entry checklist", "Walk me through the full 8-point CLS entry checklist. I want to make sure I know every criterion."),
    ("🔒 DDL protocol", "What's the exact protocol when I hit the DDL? Walk me through it step by step — what to do and what never to do."),
    ("📈 Read this market", "Based on the CLS manipulation cycle, how should I be reading the current market structure? What phase are we likely in?"),
    ("🧨 Revenge trade fix", "I just took a revenge trade. Call me out and give me the exact mindset protocol to reset right now."),
    ("💡 FU candle criteria", "What exactly makes a valid FU candle by Mr. Casino standards? Give me all the criteria."),
]


def _call_api(messages: list, system: str, stream: bool = False):
    import anthropic
    client = anthropic.Anthropic(api_key=_API_KEY)
    if stream:
        return client.messages.stream(
            model=_MODEL, max_tokens=2048,
            system=system, messages=messages,
        )
    resp = client.messages.create(
        model=_MODEL, max_tokens=2048,
        system=system, messages=messages,
    )
    return resp.content[0].text


@st.cache_data(ttl=1800)
def _generate_coaching_brief(trades_key: str, summaries_key: str, api_key: str) -> str:
    """Generate a proactive coaching brief based on recent trades and patterns."""
    if not api_key:
        return ""
    try:
        trades    = get_trades(7)
        summaries = get_daily_summaries(7)
        methodology = load_methodology()

        today_str = str(date.today())
        week_start = str(date.today() - timedelta(days=date.today().weekday()))

        today_trades = [t for t in trades if str(t.get("date",""))[:10] == today_str]
        week_trades  = [t for t in trades if str(t.get("date",""))[:10] >= week_start]

        total_pnl  = sum(t.get("pnl",0) or 0 for t in week_trades)
        wins       = sum(1 for t in week_trades if t.get("result")=="Win")
        losses     = sum(1 for t in week_trades if t.get("result")=="Loss")
        dur_vals   = [t["duration"] for t in week_trades if t.get("duration") is not None]
        avg_hold   = sum(dur_vals)/len(dur_vals) if dur_vals else None

        today_summary = ""
        if today_trades:
            today_pnl = sum(t.get("pnl",0) or 0 for t in today_trades)
            today_summary = f"Today's trades: {len(today_trades)} trades, ${today_pnl:+,.2f} PnL"
            for t in today_trades[:5]:
                dur = t.get('duration')
                today_summary += f"\n  - {t.get('symbol','?')} {t.get('direction','?')} ${t.get('pnl',0):+,.2f} | Hold: {dur}m | {t.get('rule_adherence','?')}"

        week_summary = (
            f"This week: {wins}W/{losses}L · ${total_pnl:+,.2f} PnL"
            + (f" · avg hold {avg_hold:.0f}m" if avg_hold else "")
        )

        ddl_hits = sum(1 for s in summaries if s.get("ddl_hit"))
        ddl_overrides = sum(1 for s in summaries if s.get("ddl_hit") and not s.get("closed_at_ddl"))

        prompt = f"""Generate a brief, direct coaching brief for Mala for {date.today().strftime('%A %B %d, %Y')}.

Performance data:
{week_summary}
{today_summary if today_summary else "No trades logged today yet."}
DDL breaches this week: {ddl_hits} (overridden: {ddl_overrides})

Structure your brief in exactly this format:

**TODAY'S FOCUS**
[One specific thing to execute on today — methodology-based, actionable]

**PATTERN ALERT**
[Name one behavioral or technical pattern showing up in the trade data — be specific, call it out directly. If no trades, speak to market conditions.]

**THIS WEEK**
[One honest sentence on the week's performance trajectory]

**THE ONE FIX**
[The single most important thing to do differently right now]

Keep it under 200 words. No fluff. Talk like you're texting a trader who needs to hear the truth, not a coach performing for an audience."""

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=f"You are Jarvis, Mala's direct trading coach. Context:\n{methodology[:4000]}",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        return f"[Brief error: {e}]"


def _render_coaching_panel():
    """Left panel: proactive coaching brief + quick prompts."""
    st.markdown(
        "<div style='color:#44445a;font-size:0.62rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.14em;margin-bottom:0.8rem'>Jarvis Coaching Brief</div>",
        unsafe_allow_html=True,
    )

    if not _API_KEY:
        st.markdown(
            "<div style='background:#0d0d20;border:1px solid #1e1e38;border-radius:10px;"
            "padding:1rem;color:#44445a;font-size:0.85rem'>Add ANTHROPIC_API_KEY to config/config.env</div>",
            unsafe_allow_html=True,
        )
    else:
        # Cache key based on today + trade count
        trades    = get_trades(7)
        summaries = get_daily_summaries(7)
        trades_key  = f"{date.today()}_{len(trades)}"
        summary_key = f"{date.today()}_{len(summaries)}"

        if st.button("↻ Refresh brief", key="brief_refresh", help="Regenerate coaching brief"):
            _generate_coaching_brief.clear()

        brief = _generate_coaching_brief(trades_key, summary_key, _API_KEY)

        if brief:
            sections = {
                "TODAY'S FOCUS":  ("#f0b429", "🎯"),
                "PATTERN ALERT":  ("#ff6b6b", "⚠"),
                "THIS WEEK":      ("#00d4ff", "📊"),
                "THE ONE FIX":    ("#00e676", "⚡"),
            }
            lines = brief.split("\n")
            current_h, buf, rendered = None, [], []
            for line in lines:
                clean = line.strip().replace("**", "")
                matched = next((k for k in sections if k in clean.upper()), None)
                if matched:
                    if current_h and buf:
                        rendered.append((current_h, " ".join(b.strip() for b in buf if b.strip())))
                    current_h, buf = matched, []
                elif current_h and line.strip():
                    buf.append(line)
            if current_h and buf:
                rendered.append((current_h, " ".join(b.strip() for b in buf if b.strip())))

            for heading, body in rendered:
                color, icon = sections.get(heading, ("#8888bb", "·"))
                is_alert = "ALERT" in heading or "FIX" in heading
                st.markdown(
                    f"<div style='background:{'#120808' if is_alert and color=='#ff6b6b' else '#0a0a18'};"
                    f"border:1px solid {'#ff6b6b33' if is_alert and color=='#ff6b6b' else '#1a1a30'};"
                    f"border-left:3px solid {color};border-radius:0 10px 10px 0;"
                    f"padding:0.75rem 0.9rem;margin-bottom:0.5rem'>"
                    f"<div style='color:{color};font-size:0.6rem;font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:0.12em;margin-bottom:0.35rem'>{icon} {heading}</div>"
                    f"<div style='color:#d0d0f0;font-size:0.86rem;line-height:1.6'>{body}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            now_str = f"Generated for {date.today().strftime('%b %d')} · refreshes every 30min"
            st.markdown(f"<div style='color:#2a2a40;font-size:0.62rem;margin-top:0.2rem'>{now_str}</div>",
                        unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Quick prompts
    st.markdown(
        "<div style='color:#44445a;font-size:0.62rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.14em;margin-bottom:0.6rem'>Quick Prompts</div>",
        unsafe_allow_html=True,
    )

    for label, prompt_text in _QUICK_PROMPTS:
        if st.button(label, key=f"qp_{label[:8]}", use_container_width=True):
            st.session_state.messages = st.session_state.get("messages", [])
            st.session_state.messages.append({"role": "user", "content": prompt_text})
            st.session_state["pending_send"] = True
            st.rerun()

    # Knowledge base status
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    total_kb = get_total_kb()
    docs     = get_doc_status()
    loaded   = sum(1 for d in docs if d["loaded"])
    with st.expander(f"Knowledge Base · {loaded}/{len(docs)} · {total_kb:.0f}KB", expanded=False):
        from collections import defaultdict
        by_cat = defaultdict(list)
        for d in docs:
            by_cat[d["category"]].append(d)
        for cat, cat_docs in sorted(by_cat.items()):
            cat_loaded = sum(1 for d in cat_docs if d["loaded"])
            st.markdown(
                f"<div style='color:#6666aa;font-size:0.65rem;text-transform:uppercase;"
                f"letter-spacing:0.1em;margin:0.5rem 0 0.15rem'>{cat} ({cat_loaded}/{len(cat_docs)})</div>",
                unsafe_allow_html=True,
            )
            for d in cat_docs:
                icon  = "●" if d["loaded"] else "○"
                color = "#00e676" if d["loaded"] else "#33334a"
                size  = f"{d['size_kb']}KB" if d["loaded"] else "missing"
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:0.1rem 0'>"
                    f"<span style='color:{color};font-size:0.75rem'>{icon} {d['doc']}</span>"
                    f"<span style='color:#333355;font-size:0.68rem;font-family:JetBrains Mono,monospace'>{size}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


def _render_chat_panel(methodology: str):
    """Right panel: full chat interface with streaming."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Header
    col_h, col_c = st.columns([4, 1])
    with col_h:
        st.markdown(
            "<div style='color:#44445a;font-size:0.62rem;font-weight:600;text-transform:uppercase;"
            "letter-spacing:0.14em;margin-bottom:0.8rem'>Jarvis Chat</div>",
            unsafe_allow_html=True,
        )
    with col_c:
        if st.button("Clear", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Conversation history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                "<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:12px;"
                "padding:1.5rem;text-align:center;color:#333355;font-size:0.85rem;margin-bottom:1rem'>"
                "Ask Jarvis anything — methodology, trade review, market read, psychology check.</div>",
                unsafe_allow_html=True,
            )
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Process pending quick prompt send
    if st.session_state.get("pending_send") and st.session_state.messages:
        del st.session_state["pending_send"]
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(last_msg["content"])
            with st.chat_message("assistant"):
                system = _SYSTEM + methodology
                api_messages = [{"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages]
                try:
                    with _call_api(api_messages, system, stream=True) as stream:
                        reply = st.write_stream(stream.text_stream)
                except Exception as e:
                    reply = f"Error: {e}"
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    # Chat input
    prompt = st.chat_input("Ask Jarvis about your trades, methodology, or market…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system = _SYSTEM + methodology
            api_messages = [{"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages]
            try:
                with _call_api(api_messages, system, stream=True) as stream:
                    reply = st.write_stream(stream.text_stream)
            except Exception as e:
                reply = f"Error connecting to Anthropic API: {e}"
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


def render_ai_advisor():
    st.markdown("""
    <div style='display:flex;align-items:baseline;gap:0.8rem;margin-bottom:1.2rem'>
      <span style='color:#f0f0f8;font-size:1.3rem;font-weight:700;letter-spacing:-0.02em'>AI Advisor</span>
      <span style='color:#252548;font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase'>Jarvis · CLS methodology</span>
    </div>
    """, unsafe_allow_html=True)

    if not _API_KEY or _API_KEY == "your_anthropic_api_key_here":
        st.markdown(
            "<div style='background:#1a1a0f;border:1px solid #f59e0b;border-radius:12px;"
            "padding:1.5rem;max-width:600px'>"
            "<div style='color:#f59e0b;font-weight:700;margin-bottom:0.5rem'>⚙ API Key Required</div>"
            "<div style='color:#d1d5db;font-size:0.9rem'>Add your Anthropic API key to "
            "<code>config/config.env</code> as <code>ANTHROPIC_API_KEY=sk-ant-...</code></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    methodology = load_methodology()

    # Two-column layout: coaching panel left, chat right
    left, right = st.columns([2, 3])
    with left:
        _render_coaching_panel()
    with right:
        _render_chat_panel(methodology)

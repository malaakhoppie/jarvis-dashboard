import json
import streamlit as st
import plotly.graph_objects as go
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from utils.airtable_client import get_daily_summaries, get_trades, get_pattern_flags

ROOT = Path(__file__).parent.parent.parent
EST  = ZoneInfo("America/New_York")

# Base theme — NO xaxis/yaxis here; pass them per-chart to avoid duplicate-key errors
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8888aa", family="JetBrains Mono, monospace", size=10),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#0c0c1a", bordercolor="#252548", font=dict(color="#f0f0f8", size=11)),
)

_AX = dict(gridcolor="#13132a", linecolor="#13132a", zeroline=False, showgrid=True)
_AX_DOLLAR = dict(gridcolor="#13132a", linecolor="#13132a", zeroline=False, showgrid=True, tickformat="$,.0f")

def _layout(**kw):
    """Merge base theme with per-chart overrides (xaxis/yaxis/etc)."""
    return {**_BASE, "xaxis": _AX, "yaxis": _AX, **kw}

def _gauge_layout(**kw):
    """Base theme without axes for gauge charts."""
    return {**_BASE, **kw}


def _load_eval_config() -> dict:
    p = ROOT / "config" / "eval_config.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _load_accounts() -> list:
    if "accounts_json_override" in st.session_state:
        return st.session_state["accounts_json_override"]
    p = ROOT / "config" / "accounts.json"
    if p.exists():
        return json.loads(p.read_text()).get("accounts", [])
    try:
        raw = st.secrets.get("ACCOUNTS_JSON", "")
        if raw:
            data = json.loads(raw)
            return data if isinstance(data, list) else data.get("accounts", [])
    except Exception:
        pass
    return []


def _kpi(label, value, sub="", color="#f0f0f8", accent="#f0b429", border_color="#1a1a2e"):
    return f"""
    <div style='background:#09090f;border:1px solid {border_color};border-radius:10px;
                padding:1rem 1.1rem;position:relative;overflow:hidden;height:100%'>
      <div style='position:absolute;top:0;left:0;width:3px;bottom:0;
                  background:{accent};opacity:0.7;border-radius:2px 0 0 2px'></div>
      <div style='color:#6666aa;font-size:0.62rem;text-transform:uppercase;
                  letter-spacing:0.13em;margin-bottom:0.4rem;padding-left:0.2rem'>{label}</div>
      <div style='color:{color};font-size:1.45rem;font-weight:700;
                  font-family:JetBrains Mono,monospace;line-height:1;padding-left:0.2rem'>{value}</div>
      <div style='color:#8888aa;font-size:0.72rem;margin-top:0.28rem;padding-left:0.2rem'>{sub}</div>
    </div>"""


def render_overview():
    cfg      = _load_eval_config()
    accounts = _load_accounts()
    summaries = get_daily_summaries(30)
    trades    = get_trades(30)
    flags     = get_pattern_flags()

    today    = summaries[0] if summaries else {}
    start_bal   = cfg.get("starting_balance", 25000)
    profit_tgt  = cfg.get("profit_target", 1250)
    ddl         = cfg.get("daily_loss_limit", 1000)

    # Pull current balance: Airtable daily summary → accounts.json → trade PnL → start_bal
    curr_bal = today.get("eval_balance") or 0
    if not curr_bal:
        acct_bal = next((a.get("current_balance", 0) for a in accounts if a.get("status") == "active"), 0)
        if acct_bal:
            curr_bal = acct_bal
        elif trades:
            curr_bal = start_bal + sum(t.get("pnl", 0) or 0 for t in trades)
        else:
            curr_bal = start_bal

    today_pnl   = today.get("pnl", 0) or 0
    # If no daily summary today, compute from today's trades
    if not today_pnl and trades:
        today_str = str(date.today())
        today_pnl = sum(t.get("pnl", 0) or 0 for t in trades
                        if str(t.get("date", ""))[:10] == today_str)

    today_wins  = today.get("wins", 0) or 0
    today_losses= today.get("losses", 0) or 0
    today_wr    = today.get("win_rate", 0) or 0
    day_grade   = today.get("day_grade") or "—"
    ddl_hit     = today.get("ddl_hit", False)

    gained      = curr_bal - start_bal
    tgt_pct     = (gained / profit_tgt * 100) if profit_tgt else 0
    days_on     = 0
    if cfg.get("first_trade_date"):
        try:
            days_on = (date.today() - date.fromisoformat(cfg["first_trade_date"])).days + 1
        except Exception:
            pass

    # ── DDL Banner ────────────────────────────────────────────────────────────
    if ddl_hit:
        st.markdown("""<div style='background:linear-gradient(135deg,#1a0505,#0d0000);
            border:1px solid #ff4444;border-radius:8px;padding:0.75rem 1.1rem;margin-bottom:1rem;
            box-shadow:0 0 24px rgba(255,68,68,0.15)'>
            <span style='color:#ff6666;font-size:0.9rem;font-weight:700;letter-spacing:0.05em'>
            ⚠  DDL BREACHED — CLOSE THE LAPTOP. SESSION IS OVER.</span></div>""",
            unsafe_allow_html=True)
    elif today_pnl < 0 and abs(today_pnl) > ddl * 0.7:
        st.markdown(f"""<div style='background:#0d0a00;border:1px solid #f0b42966;
            border-radius:8px;padding:0.75rem 1.1rem;margin-bottom:1rem'>
            <span style='color:#f0b429;font-size:0.85rem;font-weight:600'>
            ⚡  Loss ${abs(today_pnl):,.0f} — approaching DDL (${ddl:,.0f})</span></div>""",
            unsafe_allow_html=True)

    # ── Page title ────────────────────────────────────────────────────────────
    st.markdown("""<div style='margin-bottom:1.2rem;display:flex;align-items:baseline;gap:0.8rem'>
      <span style='color:#f0f0f8;font-size:1.3rem;font-weight:700;letter-spacing:-0.02em'>Overview</span>
      <span style='color:#252548;font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase'>live</span>
    </div>""", unsafe_allow_html=True)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    bal_col   = "#00e676" if gained >= 0 else "#ff4444"
    pnl_col   = "#00e676" if today_pnl >= 0 else "#ff4444"
    ddl_col   = "#ff4444" if ddl_hit else "#00e676"
    grade_col = {"A":"#00e676","B":"#00d4ff","C":"#f0b429","D":"#ff6b35","F":"#ff4444"}.get(day_grade,"#8888aa")
    bar_c     = min(tgt_pct, 100)
    b_col     = "#00e676" if tgt_pct >= 100 else "#f0b429"
    total_pnl    = sum(t.get("pnl",0) or 0 for t in trades)
    total_wins   = sum(1 for t in trades if t.get("result")=="Win")
    total_trades = len(trades)
    wr_all       = total_wins/total_trades*100 if total_trades else 0

    _prog_card = (
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:10px;"
        f"padding:1rem 1.1rem;position:relative;overflow:hidden'>"
        f"<div style='position:absolute;top:0;left:0;width:3px;bottom:0;"
        f"background:#f0b429;opacity:0.7;border-radius:2px 0 0 2px'></div>"
        f"<div style='color:#6666aa;font-size:0.62rem;text-transform:uppercase;"
        f"letter-spacing:0.13em;margin-bottom:0.4rem;padding-left:0.2rem'>Progress</div>"
        f"<div style='color:#f0f0f8;font-size:1.45rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace;line-height:1;padding-left:0.2rem'>{tgt_pct:.0f}%</div>"
        f"<div style='background:#13132a;border-radius:999px;height:4px;margin:0.5rem 0.2rem 0.3rem'>"
        f"<div style='background:linear-gradient(90deg,{b_col}88,{b_col});width:{bar_c:.0f}%;"
        f"height:4px;border-radius:999px'></div></div>"
        f"<div style='color:#8888aa;font-size:0.72rem;padding-left:0.2rem'>${profit_tgt-gained:,.0f} remaining</div>"
        f"</div>"
    )

    st.markdown(
        "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));"
        "gap:0.6rem;margin-bottom:0.8rem'>"
        + _kpi("Eval Balance", f"${curr_bal:,.0f}",
               f"{'+' if gained>=0 else ''}{gained:,.0f}  ({tgt_pct:.0f}% to target)", bal_col, accent=bal_col)
        + _prog_card
        + _kpi("Today PnL", f"{'+' if today_pnl>=0 else ''}${today_pnl:,.2f}",
               f"{today_wins}W / {today_losses}L  ·  {today_wr:.0f}% WR", pnl_col, accent=pnl_col)
        + _kpi("DDL", "HIT" if ddl_hit else "CLEAR", f"${ddl:,.0f}/day limit", ddl_col, accent=ddl_col)
        + _kpi("Day Grade", day_grade, f"Eval Day {days_on}", grade_col, accent=grade_col)
        + _kpi("30d PnL", f"{'+' if total_pnl>=0 else ''}${total_pnl:,.0f}",
               f"{wr_all:.0f}% WR  ·  {total_trades} trades", "#00e676" if total_pnl>=0 else "#ff4444")
        + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # ── Week Summary + Streak + DDL bar ──────────────────────────────────────
    _render_week_strip(trades, summaries, start_bal, ddl, today_pnl, ddl_hit)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Charts row ────────────────────────────────────────────────────────────
    ca, cb = st.columns([3, 2])

    with ca:
        st.markdown("<div style='color:#6666aa;font-size:0.62rem;text-transform:uppercase;"
                    "letter-spacing:0.13em;margin-bottom:0.5rem'>Equity Curve</div>",
                    unsafe_allow_html=True)
        if summaries:
            ss = sorted(summaries, key=lambda x: x.get("date") or "")
            dates, bals, running = [], [], start_bal
            for s in ss:
                running += s.get("pnl",0) or 0
                dates.append(s.get("date",""))
                bals.append(running)
        elif trades:
            ts = sorted(trades, key=lambda x: str(x.get("date") or ""))
            dates, bals, running = [], [], start_bal
            for t in ts:
                running += t.get("pnl",0) or 0
                dates.append(str(t.get("date",""))[:10])
                bals.append(running)
        else:
            dates, bals = [], []

        if dates:
            tgt_line  = [start_bal + profit_tgt] * len(dates)

            trail_amt = cfg.get("max_trailing_drawdown", 1000)
            mll_vals, running_max = [], start_bal
            for b in bals:
                running_max = max(running_max, b)
                mll_vals.append(min(running_max - trail_amt, start_bal))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=mll_vals,
                line=dict(color="rgba(255,68,68,0.55)", width=1.5, dash="dash"),
                mode="lines", name="MLL (trail)", showlegend=True))
            fig.add_trace(go.Scatter(x=dates, y=tgt_line, line=dict(color="rgba(0,230,118,0.4)",
                width=1, dash="dash"), mode="lines", name="Target", showlegend=True))
            fig.add_trace(go.Scatter(x=dates, y=bals, line=dict(color="#f0b429", width=2),
                mode="lines+markers", marker=dict(size=4, color="#f0b429"),
                fill="tozeroy", fillcolor="rgba(240,180,41,0.05)", name="Balance"))

            fig.update_layout(**_layout(
                yaxis=_AX_DOLLAR,
                legend=dict(orientation="h", x=0, y=1.12, font=dict(size=10, color="#8888aa"),
                            bgcolor="rgba(0,0,0,0)")),
                height=220, margin=dict(l=8,r=8,t=8,b=8))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                            key="ov_equity")
        else:
            _empty(220, "ov_equity_empty")

    with cb:
        st.markdown("<div style='color:#6666aa;font-size:0.62rem;text-transform:uppercase;"
                    "letter-spacing:0.13em;margin-bottom:0.5rem'>7-Day P&L</div>",
                    unsafe_allow_html=True)
        if summaries:
            week = sorted(summaries[:7], key=lambda x: x.get("date") or "")
            dlabels = [s.get("date","")[-5:] for s in week]
            dpnls   = [s.get("pnl",0) or 0 for s in week]
        elif trades:
            day_pnl: dict[str, float] = {}
            for t in sorted(trades, key=lambda x: str(x.get("date") or ""))[-7:]:
                d = str(t.get("date",""))[:10][-5:]
                day_pnl[d] = day_pnl.get(d, 0) + (t.get("pnl",0) or 0)
            dlabels = list(day_pnl.keys())
            dpnls   = list(day_pnl.values())
        else:
            dlabels, dpnls = [], []

        if dlabels:
            dcolors = ["#00e676" if p >= 0 else "#ff4444" for p in dpnls]
            fig = go.Figure(go.Bar(x=dlabels, y=dpnls, marker_color=dcolors,
                marker_line_width=0, width=0.55,
                text=[f"${p:+,.0f}" for p in dpnls], textposition="outside",
                textfont=dict(size=9, color="#8888aa")))
            fig.add_hline(y=0, line_color="#252548", line_width=1)
            fig.update_layout(**_layout(yaxis=_AX_DOLLAR, bargap=0.3, showlegend=False),
                height=220, margin=dict(l=8,r=8,t=8,b=8))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                            key="ov_7day")
        else:
            _empty(220, "ov_7day_empty")

    # ── Stats row ─────────────────────────────────────────────────────────────
    wins_all  = [t for t in trades if t.get("result")=="Win"]
    loss_all  = [t for t in trades if t.get("result")=="Loss"]
    wr_v      = len(wins_all)/len(trades)*100 if trades else 0
    avg_win   = sum(t.get("pnl",0) or 0 for t in wins_all)/len(wins_all) if wins_all else 0
    avg_loss  = abs(sum(t.get("pnl",0) or 0 for t in loss_all)/len(loss_all)) if loss_all else 0
    rr_v      = avg_win/avg_loss if avg_loss else 0
    rule_sc   = [t["rule_score"] for t in trades if t.get("rule_score") is not None]
    avg_rule  = sum(rule_sc)/len(rule_sc) if rule_sc else 0

    wr_col   = "#00e676" if wr_v >= 60 else ("#f0b429" if wr_v >= 40 else "#ff4444")
    rr_col   = "#00e676" if rr_v >= 2  else ("#f0b429" if rr_v >= 1  else "#ff4444")
    rule_col = "#00e676" if avg_rule >= 6 else ("#f0b429" if avg_rule >= 4 else "#ff4444")

    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.6rem'>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:12px;padding:1.1rem 1.2rem'>"
        f"<div style='color:#f0b429;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;"
        f"margin-bottom:0.4rem;font-weight:700'>Win Rate (30d)</div>"
        f"<div style='color:{wr_col};font-size:2rem;font-weight:700;font-family:JetBrains Mono,monospace;line-height:1'>"
        f"{wr_v:.0f}<span style='font-size:1rem;opacity:0.7'>%</span></div>"
        f"<div style='background:#13132a;border-radius:999px;height:4px;margin:0.5rem 0 0.3rem'>"
        f"<div style='background:{wr_col};width:{min(wr_v,100):.0f}%;height:4px;border-radius:999px'></div></div>"
        f"<div style='color:#6666aa;font-size:0.7rem'>{len(trades)} trades · {len(wins_all)}W / {len(loss_all)}L</div>"
        f"</div>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:12px;padding:1.1rem 1.2rem'>"
        f"<div style='color:#00d4ff;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;"
        f"margin-bottom:0.4rem;font-weight:700'>Avg Risk : Reward (30d)</div>"
        f"<div style='color:{rr_col};font-size:2rem;font-weight:700;font-family:JetBrains Mono,monospace;line-height:1'>"
        f"{rr_v:.2f}<span style='font-size:1rem;opacity:0.7'>R</span></div>"
        f"<div style='background:#13132a;border-radius:999px;height:4px;margin:0.5rem 0 0.3rem'>"
        f"<div style='background:{rr_col};width:{min(rr_v/5*100,100):.0f}%;height:4px;border-radius:999px'></div></div>"
        f"<div style='color:#6666aa;font-size:0.7rem'>target 2.0R+ · avg win ${avg_win:,.0f}</div>"
        f"</div>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:12px;padding:1.1rem 1.2rem'>"
        f"<div style='color:#a78bfa;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;"
        f"margin-bottom:0.4rem;font-weight:700'>Rules Followed (0–8)</div>"
        f"<div style='color:{rule_col};font-size:2rem;font-weight:700;font-family:JetBrains Mono,monospace;line-height:1'>"
        f"{avg_rule:.1f}<span style='font-size:1rem;opacity:0.7'>/8</span></div>"
        f"<div style='background:#13132a;border-radius:999px;height:4px;margin:0.5rem 0 0.3rem'>"
        f"<div style='background:{rule_col};width:{avg_rule/8*100:.0f}%;height:4px;border-radius:999px'></div></div>"
        f"<div style='color:#6666aa;font-size:0.7rem'>follow the process — target 6/8+</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Bottom row: flags + 7-day table ──────────────────────────────────────
    bot_l, bot_r = st.columns([2, 3])

    with bot_l:
        st.markdown("<div style='color:#6666aa;font-size:0.62rem;text-transform:uppercase;"
                    "letter-spacing:0.13em;margin-bottom:0.6rem'>Pattern Flags</div>",
                    unsafe_allow_html=True)
        if flags:
            for f in flags:
                sev   = f.get("severity","")
                sc    = {"High":"#ff4444","Medium":"#f0b429","Low":"#00d4ff"}.get(sev,"#8888aa")
                st.markdown(
                    f"<div style='border-left:3px solid {sc};background:#09090f;"
                    f"border-radius:0 8px 8px 0;padding:0.5rem 0.8rem;margin-bottom:0.35rem'>"
                    f"<div style='color:#f0f0f8;font-size:0.8rem;font-weight:600'>"
                    f"{f.get('pattern',f.get('flag','—'))}</div>"
                    f"<div style='color:#8888aa;font-size:0.7rem;margin-top:0.1rem'>"
                    f"{f.get('occurrences',0)}×  ·  {sev}  ·  {f.get('note','')}</div>"
                    f"</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#09090f;border:1px solid #13132a;border-radius:8px;"
                        "padding:0.8rem;color:#252548;font-size:0.8rem'>No active flags</div>",
                        unsafe_allow_html=True)

    with bot_r:
        st.markdown("<div style='color:#6666aa;font-size:0.62rem;text-transform:uppercase;"
                    "letter-spacing:0.13em;margin-bottom:0.6rem'>7-Day Summary</div>",
                    unsafe_allow_html=True)
        _7day_table(summaries)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Session Clock ─────────────────────────────────────────────────────────
    _render_session_clock_mini()

    # ── Today's Session ───────────────────────────────────────────────────────
    _render_session_trades(trades)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render_week_strip(trades, summaries, start_bal, ddl, today_pnl, ddl_hit):
    """Week summary bar, win/loss streak, and live DDL progress."""
    from datetime import timedelta

    today     = date.today()
    week_start = today - timedelta(days=today.weekday())

    week_trades = [t for t in trades
                   if str(t.get("date",""))[:10] >= str(week_start)]
    week_pnl    = sum(t.get("pnl",0) or 0 for t in week_trades)
    week_wins   = sum(1 for t in week_trades if t.get("result")=="Win")
    week_losses = sum(1 for t in week_trades if t.get("result")=="Loss")
    week_wr     = week_wins / len(week_trades) * 100 if week_trades else 0

    day_pnl: dict[str, float] = {}
    for t in week_trades:
        d = str(t.get("date",""))[:10]
        day_pnl[d] = day_pnl.get(d, 0) + (t.get("pnl",0) or 0)
    best_day  = max(day_pnl.values(), default=0)
    worst_day = min(day_pnl.values(), default=0)

    sorted_t  = sorted(trades, key=lambda x: str(x.get("date","")), reverse=True)
    streak_n  = 0
    streak_dir = None
    for t in sorted_t:
        r = t.get("result")
        if r not in ("Win","Loss"):
            break
        if streak_dir is None:
            streak_dir = r
        if r == streak_dir:
            streak_n += 1
        else:
            break
    streak_col = "#00e676" if streak_dir == "Win" else "#ff4444" if streak_dir else "#6666aa"
    streak_lbl = f"{'W' if streak_dir=='Win' else 'L'}{streak_n}" if streak_dir else "—"

    loss_today  = abs(min(today_pnl, 0))
    ddl_pct     = min(loss_today / ddl * 100, 100) if ddl else 0
    ddl_bar_col = "#ff4444" if ddl_hit else ("#f0b429" if ddl_pct > 60 else "#00e676")

    week_col  = "#00e676" if week_pnl >= 0 else "#ff4444"
    best_col  = "#00e676" if best_day >= 0 else "#ff4444"
    worst_col = "#ff4444" if worst_day < 0 else "#00e676"

    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.6rem;align-items:stretch'>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:10px;padding:0.7rem 0.9rem'>"
        f"<div style='color:#6666aa;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem'>This Week</div>"
        f"<div style='color:{week_col};font-size:1.1rem;font-weight:700;font-family:JetBrains Mono,monospace'>{'+' if week_pnl>=0 else ''}${week_pnl:,.2f}</div>"
        f"<div style='color:#8888aa;font-size:0.7rem'>{week_wins}W/{week_losses}L · {week_wr:.0f}% WR</div>"
        f"</div>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:10px;padding:0.7rem 0.9rem'>"
        f"<div style='color:#6666aa;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem'>Best Day</div>"
        f"<div style='color:{best_col};font-size:1.1rem;font-weight:700;font-family:JetBrains Mono,monospace'>{'+' if best_day>=0 else ''}${best_day:,.2f}</div>"
        f"<div style='color:#8888aa;font-size:0.7rem'>this week</div>"
        f"</div>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:10px;padding:0.7rem 0.9rem'>"
        f"<div style='color:#6666aa;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem'>Worst Day</div>"
        f"<div style='color:{worst_col};font-size:1.1rem;font-weight:700;font-family:JetBrains Mono,monospace'>{'+' if worst_day>=0 else ''}${worst_day:,.2f}</div>"
        f"<div style='color:#8888aa;font-size:0.7rem'>this week</div>"
        f"</div>"
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:10px;padding:0.7rem 0.9rem'>"
        f"<div style='color:#6666aa;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem'>Streak</div>"
        f"<div style='color:{streak_col};font-size:1.6rem;font-weight:700;font-family:JetBrains Mono,monospace;line-height:1'>{streak_lbl}</div>"
        f"<div style='color:#8888aa;font-size:0.7rem'>current run</div>"
        f"</div>"
        f"<div style='background:{'#120808' if ddl_hit else '#09090f'};border:1px solid {'#ff444444' if ddl_hit else '#1a1a2e'};border-radius:10px;padding:0.7rem 0.9rem'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.25rem'>"
        f"<span style='color:#6666aa;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em'>DDL Usage</span>"
        f"<span style='color:{ddl_bar_col};font-size:0.6rem;font-weight:700'>{'BREACHED' if ddl_hit else f'${loss_today:,.2f} / ${ddl:,.0f}'}</span>"
        f"</div>"
        f"<div style='background:#13132a;border-radius:999px;height:8px;margin-bottom:0.3rem;overflow:hidden'>"
        f"<div style='background:linear-gradient(90deg,{ddl_bar_col}88,{ddl_bar_col});"
        f"width:{ddl_pct:.1f}%;height:8px;border-radius:999px;"
        f"{'animation:ddlpulse 1s infinite' if ddl_hit else ''}'></div>"
        f"</div>"
        f"<div style='color:#8888aa;font-size:0.7rem'>{'🛑 CLOSE THE LAPTOP — DDL HIT' if ddl_hit else f'{100-ddl_pct:.0f}% remaining · ${ddl - loss_today:,.2f} left'}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_session_clock_mini():
    """Session pills: Asia / London / NY with full time ranges."""
    try:
        from utils.market_client import SESSIONS
    except Exception:
        return
    now = datetime.now(EST)
    cur = now.hour * 60 + now.minute
    pills = ""
    for s_name, (sh, sm), (eh, em), s_color in SESSIONS:
        start = sh * 60 + sm
        end   = eh * 60 + em
        is_on = (cur >= start or cur < end) if s_name == "Asia" else (start <= cur < end)
        bg     = s_color if is_on else f"{s_color}18"
        border = f"2px solid {s_color}" if is_on else f"1px solid {s_color}28"
        txt    = "#060608" if is_on else s_color
        sub    = "rgba(0,0,0,0.55)" if is_on else f"{s_color}88"
        pulse  = (
            f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;"
            f"background:#060608;margin-right:0.3rem;vertical-align:middle;"
            f"animation:pulse 2s infinite'></span>"
        ) if is_on else ""
        live = (
            f"<span style='background:rgba(0,0,0,0.2);color:#060608;font-size:0.55rem;"
            f"font-weight:800;padding:1px 5px;border-radius:3px;margin-left:0.3rem;"
            f"letter-spacing:0.08em'>LIVE</span>"
        ) if is_on else ""
        pills += (
            f"<div style='background:{bg};border:{border};border-radius:8px;"
            f"padding:0.5rem 0.9rem;text-align:center;flex:1;min-width:90px'>"
            f"<div style='color:{txt};font-size:0.65rem;font-weight:700;"
            f"letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.15rem'>"
            f"{pulse}{s_name}{live}</div>"
            f"<div style='color:{sub};font-size:0.68rem;"
            f"font-family:JetBrains Mono,monospace'>{sh:02d}:{sm:02d}–{eh:02d}:{em:02d} ET</div>"
            f"</div>"
        )
    st.markdown(
        f"<div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.5rem'>{pills}</div>",
        unsafe_allow_html=True,
    )


def _render_session_trades(trades: list[dict]):
    """Live session indicator + today's trades with refresh."""
    KILL_ZONES = [
        ("London Kill Zone",   2,  0,  5,  0, "#00d4ff"),
        ("NY Kill Zone",       7,  0, 12,  0, "#00e676"),
        ("Afternoon NY KZ",   15,  0, 16, 30, "#f0b429"),
    ]
    now = datetime.now(EST)
    today_str = str(date.today())
    cur = now.hour * 60 + now.minute

    active = None
    for kz_name, sh, sm, eh, em, kz_color in KILL_ZONES:
        if sh * 60 + sm <= cur < eh * 60 + em:
            mins_left = eh * 60 + em - cur
            active = (kz_name, kz_color, mins_left)
            break

    today_trades = [t for t in trades if str(t.get("date", ""))[:10] == today_str]
    sess_pnl    = sum(t.get("pnl", 0) or 0 for t in today_trades)
    sess_wins   = sum(1 for t in today_trades if t.get("result") == "Win")
    sess_losses = sum(1 for t in today_trades if t.get("result") == "Loss")
    pnl_col     = "#00e676" if sess_pnl >= 0 else "#ff4444"
    sign        = "+" if sess_pnl >= 0 else ""

    if active:
        kz_name, kz_color, mins_left = active
        hh, mm = divmod(mins_left, 60)
        time_left = f"{hh}h {mm}m left" if hh else f"{mm}m left"
        status_html = (
            f"<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
            f"background:{kz_color};margin-right:0.5rem;vertical-align:middle;"
            f"animation:pulse 2s infinite'></span>"
            f"<span style='color:{kz_color};font-weight:700;letter-spacing:0.08em'>{kz_name.upper()}</span>"
            f"<span style='color:#8888aa;margin-left:0.6rem;font-size:0.68rem'>{time_left}</span>"
        )
    else:
        status_html = (
            "<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
            "background:#252548;margin-right:0.5rem;vertical-align:middle'></span>"
            "<span style='color:#6666aa'>BETWEEN SESSIONS</span>"
        )

    hc, rc = st.columns([7, 1])
    with hc:
        st.markdown(
            f"<div style='display:flex;align-items:center;font-size:0.62rem;"
            f"text-transform:uppercase;letter-spacing:0.13em;margin-bottom:0.4rem'>"
            f"{status_html}</div>",
            unsafe_allow_html=True,
        )
    with rc:
        if st.button("↻", key="ov_refresh", help="Refresh from Airtable"):
            st.cache_data.clear()
            st.rerun()

    if today_trades:
        st.markdown(
            f"<div style='display:flex;gap:1.4rem;align-items:center;margin-bottom:0.5rem'>"
            f"<span style='color:{pnl_col};font-family:JetBrains Mono,monospace;"
            f"font-weight:700;font-size:0.95rem'>{sign}${sess_pnl:,.2f}</span>"
            f"<span style='color:#8888aa;font-size:0.75rem'>"
            f"{sess_wins}W / {sess_losses}L · {len(today_trades)} trade{'s' if len(today_trades)!=1 else ''} today</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='color:#252548;font-size:0.78rem;margin-bottom:0.5rem'>"
            "No trades recorded today yet</div>",
            unsafe_allow_html=True,
        )

    _trades_table(today_trades if today_trades else trades[:5])


def _empty(h: int, key: str):
    fig = go.Figure()
    fig.add_annotation(text="No data yet", x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(color="#252548", size=12))
    fig.update_layout(**_layout(), height=h, margin=dict(l=8,r=8,t=8,b=8))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def _gauge(col, value, vmin, vmax, color, title, suffix, key, threshold):
    with col:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            number=dict(suffix=suffix, valueformat=".1f",
                        font=dict(size=26, color="#f0f0f8", family="JetBrains Mono, monospace")),
            gauge=dict(
                axis=dict(range=[vmin, vmax], tickcolor="#252548",
                          tickfont=dict(size=9, color="#252548")),
                bar=dict(color=color, thickness=0.65),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                steps=[
                    dict(range=[vmin, threshold],     color="rgba(255,68,68,0.05)"),
                    dict(range=[threshold, vmax],      color=f"rgba(0,0,0,0)"),
                ],
                threshold=dict(line=dict(color="#00e676", width=2),
                               thickness=0.8, value=threshold),
            ),
            title=dict(text=title, font=dict(color="#7777aa", size=11)),
        ))
        fig.update_layout(**_gauge_layout(), height=175, margin=dict(l=16,r=16,t=24,b=8))
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False}, key=key)


def _7day_table(summaries):
    if not summaries:
        st.markdown("<div style='background:#09090f;border:1px solid #13132a;border-radius:8px;"
                    "padding:1rem;color:#252548;font-size:0.8rem'>No data yet</div>",
                    unsafe_allow_html=True)
        return
    rows = ""
    for i, s in enumerate(summaries[:7]):
        d    = s.get("date","—")
        p    = s.get("pnl",0) or 0
        w    = s.get("wins",0) or 0
        l    = s.get("losses",0) or 0
        wr_d = s.get("win_rate",0) or 0
        g    = s.get("day_grade") or "—"
        ddl_h = s.get("ddl_hit", False)
        closed = s.get("closed_at_ddl", False)
        pc   = "#00e676" if p >= 0 else "#ff4444"
        gc   = {"A":"#00e676","B":"#00d4ff","C":"#f0b429","D":"#ff6b35","F":"#ff4444"}.get(g,"#8888aa")
        di   = f'<span style="color:#ff4444;font-size:0.7rem">●</span>' if ddl_h and not closed else \
               (f'<span style="color:#00e676;font-size:0.7rem">✓</span>' if ddl_h else "")
        br   = "border-radius:0 0 8px 8px" if i == min(6, len(summaries)-1) else ""
        bt   = "border-top:none" if i > 0 else ""
        bg   = "#0c0c16" if i % 2 == 0 else "#09090f"
        rows += (
            f"<div style='display:flex;background:{bg};border:1px solid #13132a;"
            f"{bt};padding:0.4rem 0.8rem;{br}'>"
            f"<span style='color:#6666aa;font-family:JetBrains Mono,monospace;font-size:0.75rem;flex:1.3'>{d}</span>"
            f"<span style='color:{pc};font-family:JetBrains Mono,monospace;font-size:0.75rem;font-weight:600;flex:1'>{'+' if p>=0 else ''}${p:,.2f}</span>"
            f"<span style='color:#6666aa;font-size:0.73rem;flex:0.8'>{w}W/{l}L</span>"
            f"<span style='color:#6666aa;font-size:0.73rem;flex:0.55'>{wr_d:.0f}%</span>"
            f"<span style='color:{gc};font-size:0.73rem;font-weight:700;flex:0.4'>{g}</span>"
            f"<span style='flex:0.3;font-size:0.7rem'>{di}</span>"
            f"</div>"
        )
    header = (
        "<div style='display:flex;background:#060610;border:1px solid #13132a;"
        "border-radius:8px 8px 0 0;padding:0.3rem 0.8rem'>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:1.3'>Date</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:1'>PnL</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.8'>W/L</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.55'>WR</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.4'>Grd</span>"
        "<span style='color:#252548;font-size:0.6rem;flex:0.3'>DDL</span>"
        "</div>"
    )
    st.markdown(header + rows, unsafe_allow_html=True)


def _trades_table(trades):
    if not trades:
        st.markdown("<div style='background:#09090f;border:1px solid #13132a;border-radius:8px;"
                    "padding:1.2rem;text-align:center;color:#252548;font-size:0.82rem'>"
                    "No trades yet — import from Trade Log</div>", unsafe_allow_html=True)
        return
    header = (
        "<div style='display:flex;background:#060610;border:1px solid #13132a;"
        "border-radius:8px 8px 0 0;padding:0.3rem 1rem'>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:1.2'>Date</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.7'>Symbol</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.6'>Dir</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:1'>Net PnL</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.8'>Rule</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.7'>Session</span>"
        "<span style='color:#252548;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.1em;flex:0.6'>Result</span>"
        "</div>"
    )
    rows = ""
    for i, t in enumerate(trades):
        pnl   = t.get("pnl",0) or 0
        res   = t.get("result","")
        pc    = "#00e676" if pnl >= 0 else "#ff4444"
        dc    = "#00d4ff" if t.get("direction")=="Long" else "#f87171"
        rc    = "#00e676" if res=="Win" else ("#ff4444" if res=="Loss" else "#8888aa")
        rule  = t.get("rule_score")
        rbar  = ""
        if rule is not None:
            bw = int(rule / 8 * 48)
            rbar = (f"<span style='display:inline-block;width:{bw}px;height:2px;background:#f0b429;"
                    f"border-radius:999px;vertical-align:middle;margin-right:4px'></span>"
                    f"<span style='color:#8888aa;font-size:0.72rem'>{rule}/8</span>")
        else:
            rbar = "<span style='color:#252548'>—</span>"
        br = "border-radius:0 0 8px 8px" if i == len(trades)-1 else ""
        bt = "border-top:none" if i > 0 else ""
        bg = "#0c0c16" if i % 2 == 0 else "#09090f"
        rows += (
            f"<div style='display:flex;align-items:center;background:{bg};border:1px solid #13132a;"
            f"{bt};padding:0.45rem 1rem;{br}'>"
            f"<span style='color:#6666aa;font-family:JetBrains Mono,monospace;font-size:0.75rem;flex:1.2'>{str(t.get('date',''))[:10]}</span>"
            f"<span style='color:#f0f0f8;font-weight:600;font-size:0.82rem;flex:0.7'>{t.get('symbol','—')}</span>"
            f"<span style='color:{dc};font-size:0.75rem;flex:0.6'>{t.get('direction','—')}</span>"
            f"<span style='color:{pc};font-weight:700;font-family:JetBrains Mono,monospace;font-size:0.82rem;flex:1'>{'+' if pnl>=0 else ''}${pnl:,.2f}</span>"
            f"<span style='flex:0.8'>{rbar}</span>"
            f"<span style='color:#8888aa;font-size:0.75rem;flex:0.7'>{t.get('session','—')}</span>"
            f"<span style='color:{rc};font-size:0.75rem;font-weight:600;flex:0.6'>{res}</span>"
            f"</div>"
        )
    st.markdown(header + rows, unsafe_allow_html=True)

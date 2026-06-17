import streamlit as st
import plotly.graph_objects as go
from utils.airtable_client import get_trades, get_daily_summaries

_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8888aa", family="JetBrains Mono, monospace", size=10),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#0c0c1a", bordercolor="#252548", font=dict(color="#f0f0f8", size=11)),
)
_AX     = dict(gridcolor="#13132a", linecolor="#13132a", zeroline=False)
_AX_USD = dict(gridcolor="#13132a", linecolor="#13132a", zeroline=False, tickformat="$,.0f")

def _C(**kw):
    return {**_BASE, "xaxis": _AX, "yaxis": _AX, **kw}

_M = dict(l=8, r=8, t=20, b=8)

_n = [0]
def _k(s): _n[0] += 1; return f"p_{s}_{_n[0]}"

def _empty(msg, key):
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(color="#252548", size=12))
    fig.update_layout(**_C(), height=250, margin=_M)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_performance():
    st.markdown("## Performance")

    trades    = get_trades(60)
    summaries = get_daily_summaries(30)

    if not trades and not summaries:
        st.markdown("<div style='color:#6666aa;padding:2rem;text-align:center;font-size:0.85rem'>"
                    "No trade data yet.</div>", unsafe_allow_html=True)
        return

    # ── Summary metrics ───────────────────────────────────────────────────────
    total_pnl = sum(t.get("pnl", 0) or 0 for t in trades)
    wins      = [t for t in trades if t.get("result") == "Win"]
    losses    = [t for t in trades if t.get("result") == "Loss"]
    wr        = len(wins) / len(trades) * 100 if trades else 0
    avg_win   = sum(t.get("pnl", 0) or 0 for t in wins) / len(wins) if wins else 0
    avg_loss  = sum(t.get("pnl", 0) or 0 for t in losses) / len(losses) if losses else 0
    rr        = abs(avg_win / avg_loss) if avg_loss else 0
    rule_sc   = [t["rule_score"] for t in trades if t.get("rule_score") is not None]
    avg_rule  = sum(rule_sc) / len(rule_sc) if rule_sc else 0
    ddl_hits  = sum(1 for s in summaries if s.get("ddl_hit"))
    ddl_closed= sum(1 for s in summaries if s.get("ddl_hit") and s.get("closed_at_ddl"))

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    pc = "#00e676" if total_pnl >= 0 else "#ff4444"
    m1.metric("Total PnL",      f"${total_pnl:,.2f}")
    m2.metric("Win Rate",        f"{wr:.0f}%")
    m3.metric("Avg Win",         f"${avg_win:,.2f}")
    m4.metric("Avg Loss",        f"${avg_loss:,.2f}")
    m5.metric("R:R",             f"{rr:.2f}")
    m6.metric("Avg Rule Score",  f"{avg_rule:.1f}/8" if rule_sc else "—")

    st.divider()

    # ── Equity curve ──────────────────────────────────────────────────────────
    st.markdown("#### Cumulative PnL")
    if summaries:
        ss = sorted(summaries, key=lambda x: x.get("date") or "")
        dates, cum, running = [], [], 0
        for s in ss:
            running += s.get("pnl", 0) or 0
            dates.append(s.get("date", ""))
            cum.append(running)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=cum, mode="lines+markers",
            line=dict(color="#f0b429", width=2),
            marker=dict(size=4, color="#f0b429"),
            fill="tozeroy", fillcolor="rgba(240,180,41,0.06)", name="PnL"))
        fig.add_hline(y=0, line_dash="dash", line_color="#252548", line_width=1)
        fig.update_layout(**_C(yaxis=_AX_USD), height=270, margin=_M)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=_k("curve"))
    else:
        _empty("No daily summaries yet", _k("curve_e"))

    r1l, r1r = st.columns(2)

    # ── Daily win rate ────────────────────────────────────────────────────────
    with r1l:
        st.markdown("#### Daily Win Rate")
        if summaries:
            ss = sorted(summaries, key=lambda x: x.get("date") or "")
            dlabels = [s.get("date", "")[-5:] for s in ss]
            wrs     = [s.get("win_rate", 0) or 0 for s in ss]
            colors  = ["#00e676" if w >= 50 else "#ff4444" for w in wrs]
            fig = go.Figure(go.Bar(x=dlabels, y=wrs, marker_color=colors, marker_line_width=0))
            fig.add_hline(y=50, line_dash="dash", line_color="#252548", line_width=1)
            fig.update_layout(**_C(yaxis=dict(**_AX, range=[0, 100])), height=240, margin=_M)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=_k("wr"))
        else:
            _empty("No data yet", _k("wr_e"))

    # ── Rule adherence ────────────────────────────────────────────────────────
    with r1r:
        st.markdown("#### Rule Adherence")
        if trades:
            counts = {}
            for t in trades:
                a = t.get("rule_adherence") or "Not Set"
                counts[a] = counts.get(a, 0) + 1
            labels = list(counts.keys())
            values = list(counts.values())
            colors = [{"Full": "#00e676", "Partial": "#f0b429", "Poor": "#ff4444",
                       "Not Set": "#252548"}.get(l, "#8888aa") for l in labels]
            fig = go.Figure(go.Pie(labels=labels, values=values,
                marker=dict(colors=colors, line=dict(color="#09090f", width=2)),
                hole=0.6, textfont=dict(color="#f0f0f8", size=11)))
            fig.update_layout(**_C(showlegend=True,
                legend=dict(font=dict(color="#8888aa", size=10), bgcolor="rgba(0,0,0,0)")),
                height=240, margin=_M)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=_k("adh"))
        else:
            _empty("No data yet", _k("adh_e"))

    r2l, r2r = st.columns(2)

    # ── PnL by session ────────────────────────────────────────────────────────
    with r2l:
        st.markdown("#### PnL by Session")
        if trades:
            sess_pnl: dict[str, float] = {}
            for t in trades:
                s = t.get("session") or "Other"
                sess_pnl[s] = sess_pnl.get(s, 0) + (t.get("pnl", 0) or 0)
            labels = list(sess_pnl.keys())
            values = list(sess_pnl.values())
            colors = ["#00e676" if v >= 0 else "#ff4444" for v in values]
            fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, marker_line_width=0))
            fig.update_layout(**_C(), height=240, margin=_M)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=_k("sess"))
        else:
            _empty("No data yet", _k("sess_e"))

    # ── DDL discipline ────────────────────────────────────────────────────────
    with r2r:
        st.markdown("#### DDL Discipline")
        if summaries:
            total_days      = len(summaries)
            ddl_days        = sum(1 for s in summaries if s.get("ddl_hit"))
            closed_ok       = sum(1 for s in summaries if s.get("ddl_hit") and s.get("closed_at_ddl"))
            overrode        = ddl_days - closed_ok
            clean_days      = total_days - ddl_days
            fig = go.Figure(go.Bar(
                x=["Clean", "DDL — Closed", "DDL — Overrode"],
                y=[clean_days, closed_ok, overrode],
                marker_color=["#00e676", "#00d4ff", "#ff4444"],
                marker_line_width=0,
            ))
            fig.update_layout(**_C(), height=240, margin=_M)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=_k("ddl"))
            if overrode > 0:
                st.markdown(
                    f"<div style='background:#1a0505;border:1px solid #ff4444;border-radius:8px;"
                    f"padding:0.6rem 1rem;color:#ff8888;font-size:0.82rem'>"
                    f"DDL overridden <b>{overrode}×</b> — the one behavior to fix.</div>",
                    unsafe_allow_html=True)
        else:
            _empty("No data yet", _k("ddl_e"))

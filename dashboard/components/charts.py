"""
Charts — live candlestick with trade entry/exit overlays.
Futures market hours: daily halt 5-6pm ET, weekend close Fri 5pm → Sun 6pm.
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent.parent.parent
EST  = ZoneInfo("America/New_York")

TICKER_MAP = {
    "GC":  "GC=F",
    "MGC": "MGC=F",
    "ES":  "ES=F",
    "MES": "MES=F",
    "NQ":  "NQ=F",
    "MNQ": "MNQ=F",
    "YM":  "YM=F",
    "CL":  "CL=F",
}

TIMEFRAMES = {
    "1m":  ("1m",  "1d"),
    "5m":  ("5m",  "5d"),
    "15m": ("15m", "5d"),
    "1H":  ("1h",  "30d"),
    "4H":  ("4h",  "60d"),
    "1D":  ("1d",  "365d"),
}

INST_COLOR = {
    "GC": "#f0b429", "MGC": "#f0b429",
    "ES": "#00d4ff", "MES": "#00d4ff",
    "NQ": "#a78bfa", "MNQ": "#a78bfa",
    "YM": "#34d399",
    "CL": "#fb923c",
}


@st.cache_data(ttl=60)
def _fetch_ohlcv(ticker: str, interval: str, period: str) -> dict:
    """Fetch OHLCV from yfinance, convert to EST, return as lists (cache-safe)."""
    try:
        import yfinance as yf
        from zoneinfo import ZoneInfo as ZI
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return {}
        est = ZI("America/New_York")
        utc = ZI("UTC")
        if df.index.tz is not None:
            df.index = df.index.tz_convert(est)
        else:
            df.index = df.index.tz_localize(utc).tz_convert(est)
        return {
            "ts":     [str(t) for t in df.index],
            "opens":  df["Open"].tolist(),
            "highs":  df["High"].tolist(),
            "lows":   df["Low"].tolist(),
            "closes": df["Close"].tolist(),
            "vols":   df["Volume"].tolist(),
        }
    except Exception:
        return {}


def _parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    try:
        from dateutil.parser import parse as dp
        dt = dp(s)
        return dt.astimezone(EST) if dt.tzinfo else dt.replace(tzinfo=EST)
    except Exception:
        try:
            d = datetime.strptime(s[:10], "%Y-%m-%d")
            return d.replace(hour=10, tzinfo=EST)
        except Exception:
            return None


def _nearest_ts(target: datetime, ts_list: list[str]) -> str:
    best, best_diff = ts_list[0], float("inf")
    try:
        from dateutil.parser import parse as dp
        for ts in ts_list:
            try:
                dt = dp(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=EST)
                diff = abs((dt - target).total_seconds())
                if diff < best_diff:
                    best_diff, best = diff, ts
            except Exception:
                pass
    except Exception:
        pass
    return best


def render_charts():
    # ── Controls ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        symbol = st.selectbox("Symbol", list(TICKER_MAP.keys()), index=0, key="ch_sym")
    with c2:
        tf = st.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=1, key="ch_tf")
    with c3:
        days_back = st.selectbox("Trade window", ["Today", "7 days", "30 days", "All"], index=1, key="ch_days")
    with c4:
        show_vol = st.toggle("Volume", value=True, key="ch_vol")

    ticker   = TICKER_MAP[symbol]
    interval, period = TIMEFRAMES[tf]
    color    = INST_COLOR.get(symbol, "#f0f0f8")

    # ── OHLCV data ────────────────────────────────────────────────────────────
    with st.spinner(f"Loading {symbol} {tf}…"):
        ohlcv = _fetch_ohlcv(ticker, interval, period)

    if not ohlcv:
        st.markdown(
            "<div style='background:#0d0d20;border:1px solid #1e1e38;border-radius:10px;"
            "padding:1.2rem;color:#6666aa;font-size:0.9rem;margin-top:0.8rem'>"
            "Chart data unavailable — yfinance may be rate-limited, try again in a moment."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    ts = ohlcv["ts"]

    # ── Build figure ──────────────────────────────────────────────────────────
    if show_vol:
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.03, row_heights=[0.82, 0.18],
        )
        def _add(trace, **kw): fig.add_trace(trace, row=1, col=1, **kw)
        def _add_v(trace):     fig.add_trace(trace, row=2, col=1)
    else:
        fig = go.Figure()
        def _add(trace, **kw): fig.add_trace(trace, **kw)
        _add_v = None

    # Candlesticks
    _add(go.Candlestick(
        x=ts,
        open=ohlcv["opens"], high=ohlcv["highs"],
        low=ohlcv["lows"],   close=ohlcv["closes"],
        name=symbol,
        increasing_line_color="#00e676", increasing_fillcolor="rgba(0,230,118,0.09)",
        decreasing_line_color="#ff4444", decreasing_fillcolor="rgba(255,68,68,0.09)",
        whiskerwidth=0.7, line_width=1.2, showlegend=False,
        hovertemplate=(
            "<b>%{x|%b %d %H:%M}</b><br>"
            "O: %{open:,.2f}  H: %{high:,.2f}<br>"
            "L: %{low:,.2f}  C: %{close:,.2f}<extra></extra>"
        ),
    ))

    if show_vol and _add_v:
        vc = ["rgba(0,230,118,0.28)" if c >= o else "rgba(255,68,68,0.28)"
              for o, c in zip(ohlcv["opens"], ohlcv["closes"])]
        _add_v(go.Bar(
            x=ts, y=ohlcv["vols"],
            marker_color=vc, showlegend=False,
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
        ))

    # ── Trade overlays ────────────────────────────────────────────────────────
    plotted     = []
    no_price_ct = 0
    trade_err   = ""
    try:
        from utils.airtable_client import get_trades
        d_int = {"Today": 1, "7 days": 7, "30 days": 30, "All": 90}[days_back]
        all_trades = get_trades(d_int)

        sym_trades = [
            t for t in all_trades
            if (t.get("symbol") or "").upper().replace("=F", "") == symbol
        ]

        for trade in sym_trades:
            raw_ep = trade.get("entry")
            raw_xp = trade.get("exit")
            if not raw_ep or not raw_xp:
                no_price_ct += 1
                continue
            try:
                ep = float(raw_ep)
                xp = float(raw_xp)
            except (TypeError, ValueError):
                no_price_ct += 1
                continue

            pnl  = float(trade.get("pnl") or 0)
            dir_ = (trade.get("direction") or "Long").strip()
            dur  = trade.get("duration")
            sess = trade.get("session") or "—"
            rsco = trade.get("rule_score")
            cont = trade.get("contracts") or 1

            entry_dt = _parse_dt(trade.get("date") or "")
            if entry_dt is None:
                no_price_ct += 1
                continue

            exit_dt = (
                entry_dt + timedelta(minutes=float(dur))
                if dur else entry_dt + timedelta(hours=1)
            )

            x_e  = _nearest_ts(entry_dt, ts)
            x_x  = _nearest_ts(exit_dt,  ts)
            win  = pnl >= 0
            lc   = "#00e676" if win else "#ff4444"
            esym = "triangle-up" if dir_ == "Long" else "triangle-down"
            sign = "+" if win else ""

            _add(go.Scatter(
                x=[x_e, x_x], y=[ep, xp], mode="lines",
                line=dict(color=lc, width=2, dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))
            _add(go.Scatter(
                x=[x_e], y=[ep], mode="markers",
                marker=dict(symbol=esym, size=15, color="#00cfff",
                            line=dict(color="#f0f0f8", width=1.2)),
                showlegend=False,
                hovertemplate=(
                    f"<b>ENTRY — {dir_}</b><br>Price: {ep:,.2f}<br>"
                    f"Session: {sess}<br>Contracts: {cont}"
                    + (f"<br>Rule score: {rsco}/8" if rsco else "")
                    + "<extra></extra>"
                ),
            ))
            _add(go.Scatter(
                x=[x_x], y=[xp], mode="markers",
                marker=dict(symbol="circle", size=11, color=lc,
                            line=dict(color="#f0f0f8", width=1.2)),
                showlegend=False,
                hovertemplate=(
                    f"<b>EXIT</b><br>Price: {xp:,.2f}<br>PnL: {sign}${pnl:,.2f}"
                    + (f"<br>Duration: {dur}m" if dur else "")
                    + "<extra></extra>"
                ),
            ))
            fig.add_annotation(
                x=x_e, y=(ep + xp) / 2,
                text=f"{sign}${pnl:,.0f}",
                font=dict(color=lc, size=10, family="JetBrains Mono, monospace"),
                showarrow=False, bgcolor="#09090f", bordercolor=lc,
                borderwidth=1, borderpad=3, xanchor="left", xshift=20, opacity=0.95,
            )
            plotted.append(trade)

    except Exception as e:
        trade_err = str(e)

    # ── Legend note ────────────────────────────────────────────────────────────
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.0, y=1.0,
        text=(
            "▲ entry (blue)  ● exit  ··· connecting line  "
            "| Futures: daily halt 5–6 PM ET · closes Fri 5 PM, opens Sun 6 PM ET"
        ),
        showarrow=False,
        font=dict(color="#5555aa", size=9, family="JetBrains Mono, monospace"),
        xanchor="left", yanchor="bottom",
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    BASE = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#08080f",
        font=dict(color="#8888bb", family="JetBrains Mono, monospace", size=10),
        dragmode="pan",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0c0c1a", bordercolor="#252548",
                        font=dict(color="#f0f0f8", size=11)),
        margin=dict(l=8, r=8, t=28, b=8),
        height=460 if show_vol else 380,
    )
    AX = dict(
        gridcolor="#13132a", linecolor="#1a1a30",
        zeroline=False, showgrid=True, tickfont=dict(size=9),
    )

    if show_vol:
        fig.update_layout(
            **BASE,
            xaxis_rangeslider_visible=False,
            xaxis=dict(**AX, showticklabels=False),
            yaxis=dict(**AX, tickformat="$,.1f",
                       title=dict(text=symbol, font=dict(size=9, color="#6666aa"))),
            xaxis2=AX,
            yaxis2=dict(**AX, title=dict(text="Vol", font=dict(size=9, color="#6666aa"))),
        )
    else:
        fig.update_layout(
            **BASE,
            xaxis_rangeslider_visible=False,
            xaxis=AX,
            yaxis=dict(**AX, tickformat="$,.1f"),
        )

    st.plotly_chart(fig, use_container_width=True, config={
        "scrollZoom": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["autoScale2d", "lasso2d", "select2d"],
    })

    # ── Trade table ──────────────────────────────────────────────────────────
    if plotted:
        _render_trade_table(plotted)
    else:
        if trade_err:
            st.markdown(
                f"<div style='color:#ff6b6b;font-size:0.78rem;margin-top:0.5rem'>"
                f"Trade overlay error: {trade_err}</div>",
                unsafe_allow_html=True,
            )
        elif no_price_ct:
            st.markdown(
                f"<div style='color:#f0b429;font-size:0.78rem;margin-top:0.5rem'>"
                f"{no_price_ct} {symbol} trade(s) found but missing Entry Price / Exit Price — "
                f"add those fields in the Trade Log to show them on the chart.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='color:#5555aa;font-size:0.8rem;margin-top:0.5rem'>"
                "No trades logged for this symbol in the selected window.</div>",
                unsafe_allow_html=True,
            )


def _render_market_banner():
    try:
        from utils.market_client import get_market_status
        status  = get_market_status()
        is_open = status["open"]
        color   = "#00e676" if is_open else "#ff6b6b"
        label   = "MARKET OPEN" if is_open else "MARKET CLOSED"
        detail  = status["detail"]
        pulse   = "animation:pulse 2s infinite;" if is_open else ""
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.7rem;"
            f"background:#09090f;border:1px solid #1a1a2e;border-radius:8px;"
            f"padding:0.5rem 0.9rem;margin-bottom:0.6rem'>"
            f"<div style='width:8px;height:8px;border-radius:50%;background:{color};"
            f"box-shadow:0 0 7px {color}88;flex-shrink:0;{pulse}'></div>"
            f"<span style='color:{color};font-size:0.72rem;font-weight:700;"
            f"letter-spacing:0.1em'>{label}</span>"
            f"<span style='color:#6666aa;font-size:0.72rem;margin-left:0.3rem'>{detail}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def _render_trade_table(trades: list[dict]):
    st.markdown(
        "<div style='color:#6666aa;font-size:0.62rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.14em;margin:1rem 0 0.5rem;padding-bottom:0.3rem;"
        "border-bottom:1px solid #1a1a2e'>TRADES ON CHART</div>",
        unsafe_allow_html=True,
    )

    header = (
        "<div style='display:grid;grid-template-columns:1fr 0.7fr 0.7fr 1.6fr 1fr 1fr;"
        "padding:0.4rem 0.9rem;background:#0c0c18;font-size:0.62rem;font-weight:700;"
        "text-transform:uppercase;letter-spacing:0.1em;color:#6666aa'>"
        "<span>Date</span><span>Sym</span><span>Dir</span>"
        "<span>Entry → Exit</span><span>PnL</span><span>Session · Dur</span>"
        "</div>"
    )

    rows = ""
    for t in trades:
        pnl  = float(t.get("pnl") or 0)
        win  = pnl >= 0
        lc   = "#00e676" if win else "#ff4444"
        sign = "+" if win else ""
        dir_ = t.get("direction") or "—"
        ep   = float(t.get("entry") or 0)
        xp   = float(t.get("exit")  or 0)
        dc   = "#00cfff" if dir_ == "Long" else "#f0b429"
        rows += (
            f"<div style='display:grid;grid-template-columns:1fr 0.7fr 0.7fr 1.6fr 1fr 1fr;"
            f"padding:0.5rem 0.9rem;border-bottom:1px solid #111120;font-size:0.82rem;"
            f"align-items:center'>"
            f"<span style='color:#8888bb'>{str(t.get('date') or '')[:10]}</span>"
            f"<span style='color:#f0f0f8;font-weight:600'>{t.get('symbol','—')}</span>"
            f"<span style='color:{dc}'>{dir_}</span>"
            f"<span style='color:#8888bb;font-family:JetBrains Mono,monospace'>"
            f"{ep:,.2f} → {xp:,.2f}</span>"
            f"<span style='color:{lc};font-family:JetBrains Mono,monospace;font-weight:700'>"
            f"{sign}${pnl:,.2f}</span>"
            f"<span style='color:#8888aa;font-size:0.78rem'>"
            f"{t.get('session','—')} · {t.get('duration','—')}m</span>"
            f"</div>"
        )

    st.markdown(
        f"<div style='background:#09090f;border:1px solid #1a1a2e;border-radius:10px;"
        f"overflow:hidden'>{header}{rows}</div>",
        unsafe_allow_html=True,
    )

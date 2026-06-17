import json
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.airtable_client import get_trades, create_trade, get_last_post_error
from utils.tradovate_client import get_fills, credentials_status
from utils.tradovate_csv import parse_tradovate_csv, parse_tradovate_pdf, fills_to_airtable_fields

ROOT = Path(__file__).parent.parent.parent


def _auto_update_balance(net_pnl: float, account_id: str | None = None):
    """Update current_balance in accounts.json and/or session_state."""
    changed = False

    def _apply(accts: list) -> bool:
        for acct in accts:
            match = (account_id and acct.get("id") == account_id) or (not account_id and acct.get("status") == "active")
            if match:
                old = acct.get("current_balance", acct.get("starting_balance", 0))
                new = old + net_pnl
                acct["current_balance"] = round(new, 2)
                acct["highest_balance"] = round(max(new, acct.get("highest_balance", new)), 2)
                return True
        return False

    # Local file
    try:
        path = ROOT / "config" / "accounts.json"
        if path.exists():
            data = json.loads(path.read_text())
            if _apply(data.get("accounts", [])):
                path.write_text(json.dumps(data, indent=2))
                changed = True
    except Exception:
        pass

    # Cloud session_state
    if "accounts_json_override" in st.session_state:
        accts = st.session_state["accounts_json_override"]
        if _apply(accts):
            st.session_state["accounts_json_override"] = accts
            changed = True

    return changed


def _push_daily_summaries(trades: list[dict], pnl_fn) -> tuple[int, int]:
    """Create a daily summary in Airtable for each day in the imported trade list."""
    from utils.airtable_client import create_daily_summary
    day_map: dict[str, list] = {}
    for t in trades:
        d = str(t.get("date", ""))[:10]
        if d:
            day_map.setdefault(d, []).append(t)
    saved = failed = 0
    for d, day_trades in day_map.items():
        pnls  = [pnl_fn(t) for t in day_trades]
        total = round(sum(pnls), 2)
        wins  = sum(1 for p in pnls if p > 0)
        losses= sum(1 for p in pnls if p < 0)
        n     = len(pnls)
        wr    = round(wins / n * 100, 1) if n else 0
        fields = {
            "Date":          d + "T00:00:00.000Z",
            "Total PnL ($)": total,
            "Trades Taken":  n,
            "Wins":          wins,
            "Losses":        losses,
            "Win Rate (%)":  wr,
            "DDL Hit":       False,
            "Closed at DDL": False,
        }
        if create_daily_summary(fields):
            saved += 1
        else:
            failed += 1
    return saved, failed


def _load_accounts() -> list[dict]:
    try:
        path = ROOT / "config" / "accounts.json"
        return json.loads(path.read_text()).get("accounts", [])
    except Exception:
        return []


def render_trade_log():
    st.markdown("## Trade Log")

    creds = credentials_status()

    if creds["set"]:
        tab_at, tab_tv, tab_import, tab_add = st.tabs(["Airtable Log", "Tradovate Live", "Import CSV/PDF", "Log Trade"])
    else:
        tab_at, tab_import, tab_add = st.tabs(["Airtable Log", "Import CSV/PDF", "Log Trade"])
        tab_tv = None

    with tab_at:
        _render_airtable_trades()

    if tab_tv is not None:
        with tab_tv:
            _render_tradovate_fills()

    with tab_import:
        _render_csv_import()

    with tab_add:
        _render_add_form()


def _render_airtable_trades():
    trades = get_trades(60)

    with st.expander("Filters", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            symbols = ["All"] + sorted({t["symbol"] for t in trades if t.get("symbol")})
            sym_filter = st.selectbox("Symbol", symbols, key="at_sym")
        with fc2:
            sessions = ["All"] + sorted({t["session"] for t in trades if t.get("session")})
            sess_filter = st.selectbox("Session", sessions, key="at_sess")
        with fc3:
            results = ["All", "Win", "Loss", "BE"]
            result_filter = st.selectbox("Result", results, key="at_result")

    filtered = trades
    if sym_filter != "All":
        filtered = [t for t in filtered if t.get("symbol") == sym_filter]
    if sess_filter != "All":
        filtered = [t for t in filtered if t.get("session") == sess_filter]
    if result_filter != "All":
        filtered = [t for t in filtered if t.get("result") == result_filter]

    if filtered:
        total_pnl = sum(t.get("pnl", 0) or 0 for t in filtered)
        wins = sum(1 for t in filtered if t.get("result") == "Win")
        losses = sum(1 for t in filtered if t.get("result") == "Loss")
        wr = (wins / len(filtered) * 100) if filtered else 0
        avg_rule = [t["rule_score"] for t in filtered if t.get("rule_score") is not None]
        avg_rule_score = sum(avg_rule) / len(avg_rule) if avg_rule else 0

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Total PnL", f"${total_pnl:,.2f}")
        sc2.metric("Win Rate", f"{wr:.0f}%", f"{wins}W / {losses}L")
        sc3.metric("Trades", len(filtered))
        sc4.metric("Avg Rule Score", f"{avg_rule_score:.1f}/8" if avg_rule else "—")
        st.divider()

    if filtered:
        for t in filtered:
            pnl = t.get("pnl", 0) or 0
            pnl_col = "#00e676" if pnl >= 0 else "#ff4444"
            dir_col = "#00d4ff" if t.get("direction") == "Long" else "#f87171"
            adh = t.get("rule_adherence", "")
            adh_col = {"Full": "#00e676", "Partial": "#f59e0b", "None": "#ff4444"}.get(adh, "#8888aa")
            rule = t.get("rule_score")
            rule_txt = f"{rule}/8" if rule is not None else "—"
            ddl = t.get("ddl_status", "")
            ddl_col = "#ff4444" if ddl == "Hit" else "#00e676" if ddl == "Clear" else "#8888aa"

            st.markdown(
                f"<div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.4rem'>"
                f"<div style='display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap'>"
                f"<span style='color:#8888aa;font-family:JetBrains Mono,monospace;font-size:0.78rem;min-width:90px'>{str(t.get('date',''))[:10]}</span>"
                f"<span style='color:#f0f0f8;font-weight:700;min-width:55px'>{t.get('symbol','—')}</span>"
                f"<span style='background:{dir_col}22;color:{dir_col};padding:1px 8px;border-radius:999px;font-size:0.75rem;min-width:50px;text-align:center'>{t.get('direction','—')}</span>"
                f"<span style='color:{pnl_col};font-weight:700;font-family:JetBrains Mono,monospace;min-width:80px'>{'+' if pnl >= 0 else ''}${pnl:,.2f}</span>"
                f"<span style='color:#8888aa;font-size:0.78rem'>Rule <span style='color:#f0f0f8'>{rule_txt}</span></span>"
                f"<span style='color:{adh_col};font-size:0.78rem'>{adh}</span>"
                f"<span style='color:#8888aa;font-size:0.78rem'>{t.get('session','')}</span>"
                f"<span style='color:{ddl_col};font-size:0.72rem'>{ddl}</span>"
                f"</div>"
                + (f"<div style='color:#44445a;font-size:0.74rem;margin-top:0.35rem;padding-top:0.3rem;border-top:1px solid #1a1a2e'>{t.get('notes','')}</div>" if t.get("notes") else "")
                + "</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("<div style='color:#44445a;padding:2rem;text-align:center;font-size:0.85rem'>No trades found. Log your first trade in the Log Trade tab.</div>", unsafe_allow_html=True)


def _render_tradovate_fills():
    """Display fills pulled directly from Tradovate — no manual entry needed."""
    st.markdown("""
    <div style='color:#8888aa;font-size:0.8rem;margin-bottom:1rem'>
      Live fills from Tradovate. Updates every 60 seconds. Click a fill to annotate it in the Airtable log.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Filters", expanded=False):
        tv_days = st.selectbox("Look back", [1, 7, 14, 30], index=1, key="tv_days")

    fills = get_fills(tv_days)

    if not fills:
        st.markdown("<div style='color:#44445a;padding:2rem;text-align:center;font-size:0.85rem'>No fills found. Make sure your Tradovate credentials are correct and you have traded in the selected period.</div>", unsafe_allow_html=True)
        return

    st.markdown(f"<div style='color:#8888aa;font-size:0.78rem;margin-bottom:0.6rem'>{len(fills)} fills · last {tv_days} day(s)</div>", unsafe_allow_html=True)

    for f in fills:
        side = f.get("side", "—")
        side_color = "#00d4ff" if side == "Buy" else "#f87171"
        ts = f.get("timestamp", "")
        try:
            from datetime import timezone
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts_fmt = ts_dt.astimezone().strftime("%m/%d %H:%M:%S")
        except Exception:
            ts_fmt = ts[:16]
        commission = f.get("commission", 0)

        st.markdown(
            f"<div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:10px;padding:0.7rem 1.1rem;margin-bottom:0.35rem'>"
            f"<div style='display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap'>"
            f"<span style='color:#44445a;font-family:JetBrains Mono,monospace;font-size:0.75rem;min-width:120px'>{ts_fmt}</span>"
            f"<span style='color:#f0f0f8;font-weight:700;min-width:60px'>{f.get('symbol','—')}</span>"
            f"<span style='background:{side_color}22;color:{side_color};padding:1px 8px;border-radius:999px;font-size:0.75rem;min-width:40px;text-align:center'>{side}</span>"
            f"<span style='color:#f0f0f8;font-family:JetBrains Mono,monospace'>@ {f.get('price',0):,.4f}</span>"
            f"<span style='color:#8888aa;font-size:0.78rem'>×{f.get('qty',0)}</span>"
            + (f"<span style='color:#44445a;font-size:0.72rem'>comm: ${commission:,.2f}</span>" if commission else "")
            + f"<span style='color:#252548;font-family:JetBrains Mono,monospace;font-size:0.68rem;margin-left:auto'>#{f.get('fill_id','')}</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if st.button("Import Selected to Airtable Log", key="tv_import"):
        st.info("Select fills above and annotate them, then save to Airtable. (Full import workflow coming in next build.)")


def _render_add_form():
    """Manual trade entry form → saves to Airtable."""
    st.markdown("<div style='color:#8888aa;font-size:0.8rem;margin-bottom:1rem'>Log a trade manually with full methodology scoring.</div>", unsafe_allow_html=True)

    with st.form("add_trade", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            trade_date = st.date_input("Date", value=datetime.today())
            symbol = st.selectbox("Symbol", ["MES", "MGC", "MNQ", "ES", "NQ", "YM", "RTY", "CL", "GC", "Other"])
        with f2:
            direction = st.selectbox("Direction", ["Long", "Short"])
            session = st.selectbox("Session", ["NY", "London", "NY-London Overlap", "Asia", "After Hours"])
        with f3:
            entry_price = st.number_input("Entry Price", min_value=0.0, step=0.25)
            exit_price  = st.number_input("Exit Price",  min_value=0.0, step=0.25)

        f4, f5, f6 = st.columns(3)
        with f4:
            contracts  = st.number_input("Contracts", min_value=1, step=1, value=1)
            pnl        = st.number_input("PnL ($)", step=0.01)
        with f5:
            duration   = st.number_input("Duration (min)", min_value=0, step=1)
            rule_score = st.slider("Rule Score (0-8)", 0, 8, 4)
        with f6:
            result         = st.selectbox("Result", ["Win", "Loss", "BE"])
            ddl_status     = st.selectbox("DDL Status", ["No DDL", "DDL Hit - Closed", "DDL Hit - OVERRODE"])
            rule_adherence = st.selectbox("Rule Adherence", ["Full", "Partial", "None"])

        setup_tags = st.multiselect(
            "Setup Tags",
            ["FU Candle", "HCS", "LAL", "Liquidity Grab", "Displacement", "FVG", "BOS", "HTF Aligned", "LTF Entry Model"],
        )
        notes = st.text_area("Notes", height=80)

        submitted = st.form_submit_button("Save Trade", use_container_width=True)
        if submitted:
            trade_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"
            fields = {
                "Trade ID":           trade_id,
                "Date":               datetime.combine(trade_date, datetime.min.time()).isoformat() + "Z",
                "Symbol":             symbol,
                "Direction":          direction,
                "Entry Price":        float(entry_price),
                "Exit Price":         float(exit_price),
                "Contracts":          int(contracts),
                "PnL ($)":            float(pnl),
                "Duration (min)":     int(duration),
                "Session":            session,
                "Setup Tags":         setup_tags,
                "Rule Score (0-8)":   int(rule_score),
                "DDL Status":         ddl_status,
                "Rule Adherence":     rule_adherence,
                "Result":             result,
                "Source":             "Manual",
                "Notes":              notes,
            }
            if create_trade(fields):
                st.success(f"Trade {trade_id} saved.")
                st.rerun()
            else:
                err = get_last_post_error()
                st.error(f"Failed to save — {err}" if err else "Failed to save. Check Settings → Airtable Tables.")


def _render_csv_import():
    """Import Tradovate CSV or PDF account report directly into the dashboard."""
    st.markdown("""
    <div style='color:#8888aa;font-size:0.82rem;margin-bottom:1rem'>
      Download your account report from <b style='color:#f0f0f8'>trader.tradovate.com → Account → Reports → Account Statement</b>
      then upload the CSV or PDF here. Trades appear instantly in your log.
    </div>
    """, unsafe_allow_html=True)

    # Account selector
    accts = _load_accounts()
    selected_acct_id = None
    if accts:
        acct_labels = [f"{a.get('label','?')} ({a.get('firm','?')} · {a.get('type','?').upper()})" for a in accts]
        acct_ids    = [a["id"] for a in accts]
        # Default to first active account
        default_idx = next((i for i, a in enumerate(accts) if a.get("status") == "active"), 0)
        chosen_label = st.selectbox(
            "Apply trades to account",
            acct_labels,
            index=default_idx,
            key="import_account_sel",
            help="Balance update after import will apply to this account.",
        )
        selected_acct_id = acct_ids[acct_labels.index(chosen_label)]

    uploaded = st.file_uploader(
        "Upload Tradovate Report",
        type=["csv", "pdf"],
        help="Download from: trader.tradovate.com → Account → Reports → Account Statement",
    )

    if not uploaded:
        # Show instructions
        st.markdown("""
        <div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:10px;padding:1.2rem;margin-top:0.5rem'>
          <div style='color:#f0b429;font-size:0.82rem;font-weight:600;margin-bottom:0.6rem'>How to get your report:</div>
          <div style='color:#8888aa;font-size:0.8rem;line-height:1.7'>
            1. Go to <span style='color:#00d4ff'>trader.tradovate.com</span><br>
            2. Click <b style='color:#f0f0f8'>Account</b> in the top menu<br>
            3. Click <b style='color:#f0f0f8'>Reports</b><br>
            4. Select <b style='color:#f0f0f8'>Account Statement</b> or <b style='color:#f0f0f8'>Trade History</b><br>
            5. Set date range → Export as <b style='color:#f0f0f8'>CSV</b> or <b style='color:#f0f0f8'>PDF</b><br>
            6. Upload the file here
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Parse
    with st.spinner("Parsing report..."):
        content = uploaded.read()
        if uploaded.name.endswith(".pdf"):
            trades = parse_tradovate_pdf(content)
        else:
            trades = parse_tradovate_csv(content)

    if not trades:
        st.error("Could not parse this file. Make sure it's a Tradovate Performance or Account Statement export (CSV or PDF).")
        return

    st.success(f"Parsed {len(trades)} trade(s).")

    # ── Commission settings ───────────────────────────────────────────────────
    # Tradovate Performance CSV only has GROSS PnL — fees must be applied manually.
    # Account Statement CSV includes commission per fill (already net).
    is_performance_csv = any(t.get("source") == "Tradovate Performance CSV" for t in trades)
    has_builtin_fees = any((t.get("commission") or 0) != 0 for t in trades)

    if is_performance_csv and not has_builtin_fees:
        st.markdown("""
        <div style='background:#0c0c14;border:1px solid #f0b429;border-radius:8px;
                    padding:0.8rem 1rem;margin-bottom:0.8rem'>
          <div style='color:#f0b429;font-size:0.8rem;font-weight:600;margin-bottom:0.2rem'>
            ⚡ Performance CSV — Enter commission to get net PnL
          </div>
          <div style='color:#8888aa;font-size:0.75rem'>
            Tradovate Performance report shows gross PnL only. Enter your commission rate
            and the dashboard will calculate your net PnL automatically.
            <br>Funded Next (Tradovate): MGC ≈ $1.21/side · MES ≈ $0.57/side · NQ ≈ $1.28/side
          </div>
        </div>""", unsafe_allow_html=True)

        cc1, cc2 = st.columns([1, 2])
        with cc1:
            comm_per_side = st.number_input(
                "Commission per contract per side ($)",
                min_value=0.0, max_value=10.0, value=1.21, step=0.01,
                key="import_comm_rate",
                help="Tradovate charges this per contract per fill. A round-trip = 2 sides.",
            )
        with cc2:
            # Show what total fees will be
            total_contracts = sum(t.get("qty", 1) for t in trades)
            total_fee = comm_per_side * total_contracts * 2
            st.markdown(f"""
            <div style='background:#060608;border:1px solid #1a1a2e;border-radius:8px;
                        padding:0.7rem 1rem;margin-top:1.6rem'>
              <span style='color:#44445a;font-size:0.78rem'>Estimated total fees: </span>
              <span style='color:#ff4444;font-family:JetBrains Mono,monospace;font-size:0.88rem;font-weight:600'>
                -${total_fee:,.2f}
              </span>
              <span style='color:#44445a;font-size:0.72rem'>
                &nbsp;({total_contracts} contracts × 2 sides × ${comm_per_side:.2f})
              </span>
            </div>""", unsafe_allow_html=True)
    else:
        comm_per_side = 0.0

    # Apply commission to get net PnL for each trade
    def _net_pnl(t: dict) -> float:
        gross = t.get("pnl") or 0
        if comm_per_side > 0:
            return gross - (comm_per_side * (t.get("qty") or 1) * 2)
        # For Account Statement format, fee is already in commission field
        return gross - (t.get("commission") or 0)

    # ── Preview table ─────────────────────────────────────────────────────────
    st.markdown("<div style='color:#44445a;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;margin:0.8rem 0 0.4rem'>Preview</div>", unsafe_allow_html=True)

    gross_total = sum(t.get("pnl") or 0 for t in trades)
    net_total = sum(_net_pnl(t) for t in trades)
    total_fees = gross_total - net_total
    wins = sum(1 for t in trades if _net_pnl(t) > 0)
    losses = sum(1 for t in trades if _net_pnl(t) < 0)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Trades", len(trades))
    m2.metric("Gross PnL", f"${gross_total:,.2f}")
    m3.metric("Fees", f"-${total_fees:,.2f}" if total_fees > 0 else "$0")
    m4.metric("Net PnL", f"${net_total:,.2f}")
    m5.metric("W / L", f"{wins} / {losses}")

    for t in trades[:20]:
        gross = t.get("pnl") or 0
        net = _net_pnl(t)
        fee = gross - net
        pnl_col = "#00e676" if net >= 0 else "#ff4444"
        dir_col = "#00d4ff" if t.get("direction") == "Long" else "#f87171"
        direction = t.get("direction", t.get("side", "—"))
        st.markdown(
            f"<div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:8px;"
            f"padding:0.55rem 1rem;margin-bottom:0.25rem;display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap'>"
            f"<span style='color:#44445a;font-family:JetBrains Mono,monospace;font-size:0.73rem;min-width:130px'>{t.get('date','')} {t.get('time','')[:5]}</span>"
            f"<span style='color:#f0f0f8;font-weight:600;min-width:50px'>{t.get('symbol','—')}</span>"
            f"<span style='color:{dir_col};background:{dir_col}22;padding:1px 8px;border-radius:999px;font-size:0.73rem'>{direction}</span>"
            f"<span style='color:#8888aa;font-size:0.75rem'>×{t.get('qty', t.get('contracts', 1))}</span>"
            f"<span style='color:#44445a;font-family:JetBrains Mono,monospace;font-size:0.78rem'>gross ${gross:+,.2f}</span>"
            + (f"<span style='color:#ff4444;font-size:0.75rem'>fee -${fee:,.2f}</span>" if fee > 0 else "")
            + f"<span style='color:{pnl_col};font-family:JetBrains Mono,monospace;font-size:0.88rem;font-weight:700;margin-left:auto'>net {'+' if net>=0 else ''}${net:,.2f}</span>"
            f"<span style='color:#44445a;font-size:0.72rem'>{t.get('session','')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    if len(trades) > 20:
        st.markdown(f"<div style='color:#44445a;font-size:0.75rem;margin-top:0.3rem'>... and {len(trades)-20} more</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Import options ────────────────────────────────────────────────────────
    ic1, ic2 = st.columns(2)
    with ic1:
        default_rule = st.slider("Default rule score for all imports", 0, 8, 4, key="import_rule")
    with ic2:
        skip_zero = st.checkbox("Skip zero-PnL rows", value=True, key="import_skip_zero")

    if st.button("Import to Airtable Log", key="csv_import_btn", use_container_width=True):
        to_import = [t for t in trades if not (skip_zero and abs(_net_pnl(t)) < 0.01)]
        saved = 0
        failed = 0
        prog = st.progress(0)
        for i, fill in enumerate(to_import):
            # Overwrite pnl with net value before mapping to Airtable
            fill_with_net = dict(fill)
            fill_with_net["pnl"] = _net_pnl(fill)
            fill_with_net["commission"] = gross_total - net_total if i == 0 else (fill.get("commission") or comm_per_side * (fill.get("qty") or 1) * 2)
            result_str = "Win" if fill_with_net["pnl"] > 0 else ("Loss" if fill_with_net["pnl"] < 0 else "BE")
            fields = fills_to_airtable_fields(fill_with_net, rule_score=default_rule, result=result_str)
            if create_trade(fields):
                saved += 1
            else:
                failed += 1
            prog.progress((i + 1) / len(to_import))

        if saved:
            st.success(f"Imported {saved} trade(s) to Airtable.")
            if _auto_update_balance(net_total, selected_acct_id):
                st.info(f"Balance updated: {'+' if net_total >= 0 else ''}${net_total:,.2f} applied.")
            ds_saved, ds_failed = _push_daily_summaries(to_import, _net_pnl)
            if ds_saved:
                st.info(f"Daily summary created for {ds_saved} trading day(s) — Overview will now reflect today's stats.")
            elif ds_failed:
                st.warning("Trades imported but daily summary failed — Overview metrics may show incomplete data.")
            st.rerun()
        if failed:
            err = get_last_post_error()
            detail = f" — {err}" if err else " — check Settings → Airtable Tables for connection details."
            st.error(f"{failed} trade(s) failed{detail}")

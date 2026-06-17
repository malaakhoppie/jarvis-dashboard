"""
Accounts — prop firm evals, funded, live, demo, and paper accounts.
"""
import json
import re
import streamlit as st
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent

ACCOUNT_TYPES   = ["eval", "funded", "live", "demo", "paper"]
CHALLENGE_TYPES = ["n/a", "1-step", "2-step", "instant"]
ASSET_CLASSES   = ["Futures", "Forex", "Stocks", "Crypto", "Options"]
PLATFORMS       = ["Tradovate", "NinjaTrader", "MT4", "MT5", "TradeStation",
                   "ThinkorSwim", "cTrader", "IBKR", "Other"]
FIRMS_PRESETS   = ["Funded Next", "Apex", "Topstep", "FTMO", "MyFundedFX",
                   "The 5%ers", "True Trader", "Other"]
STATUSES        = ["active", "passed", "failed", "inactive", "paper"]


def _md(html: str):
    st.markdown("\n".join(ln for ln in html.split("\n") if ln.strip()), unsafe_allow_html=True)


def _load_accounts() -> list[dict]:
    path = ROOT / "config" / "accounts.json"
    if path.exists():
        return json.loads(path.read_text()).get("accounts", [])
    return []


def _save_accounts(accounts: list[dict]):
    path = ROOT / "config" / "accounts.json"
    try:
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing["accounts"] = accounts
        path.write_text(json.dumps(existing, indent=2))
    except (OSError, PermissionError):
        st.warning("Running on Streamlit Cloud — account edits are not persisted. Update accounts.json locally and redeploy.")


def _replace_account(updated: dict, all_accounts: list[dict]) -> list[dict]:
    return [updated if a["id"] == updated["id"] else a for a in all_accounts]


def _status_style(status: str) -> tuple[str, str, str]:
    return {
        "active":   ("#00e676", "#00e67622", "● ACTIVE"),
        "passed":   ("#00d4ff", "#00d4ff22", "✓ PASSED"),
        "failed":   ("#ff4444", "#ff444422", "✗ FAILED"),
        "inactive": ("#8888aa", "#8888aa22", "○ INACTIVE"),
        "paper":    ("#f0b429", "#f0b42922", "◎ PAPER"),
    }.get(status, ("#8888aa", "#8888aa22", status.upper()))


def _type_color(acct_type: str) -> str:
    return {
        "eval":   "#f0b429",
        "funded": "#00e676",
        "live":   "#00d4ff",
        "demo":   "#a855f7",
        "paper":  "#8888aa",
    }.get(acct_type, "#8888aa")


def _challenge_badge(challenge_type: str, acct_type: str) -> str:
    if acct_type not in ("eval", "funded") or not challenge_type or challenge_type == "n/a":
        return ""
    colors = {
        "1-step":  ("#00d4ff", "#00d4ff22"),
        "2-step":  ("#f0b429", "#f0b42922"),
        "instant": ("#00e676", "#00e67622"),
    }
    fg, bg = colors.get(challenge_type, ("#8888aa", "#8888aa22"))
    return (
        f"<span style='background:{bg};color:{fg};padding:2px 8px;border-radius:6px;"
        f"font-size:0.75rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-left:0.3rem'>{challenge_type}</span>"
    )


def _calc_floor(acct: dict) -> tuple[float, str]:
    start_bal = acct.get("starting_balance", 0)
    curr_bal  = acct.get("current_balance", start_bal)
    high_bal  = acct.get("highest_balance", max(curr_bal, start_bal))

    if acct.get("trailing_drawdown"):
        trail_amt = acct.get("trailing_drawdown_amount", acct.get("max_trailing_drawdown", 1000))
        floor_cap = acct.get("account_floor_cap", start_bal)
        raw_floor = high_bal - trail_amt
        floor     = min(raw_floor, floor_cap)
        locked    = raw_floor >= floor_cap
        label     = f"trailing ${trail_amt:,.0f} · {'LOCKED at' if locked else 'floor'} ${floor:,.0f}"
    else:
        floor = acct.get("account_floor", start_bal - acct.get("max_loss", 1500))
        label = f"static floor ${floor:,.0f}"

    return floor, label


def _mll_tracker_html(start_bal, curr_bal, high_bal, floor, floor_cap, trail_amt, floor_locked) -> str:
    lock_point  = floor_cap + trail_amt
    trail_range = lock_point - start_bal
    trail_done  = min(max(high_bal - start_bal, 0), trail_range)
    trail_pct   = min(trail_done / trail_range * 100, 100) if trail_range else 0
    to_lock     = max(0.0, lock_point - high_bal)
    mll_color   = "#00e676" if floor_locked else "#f87171"
    bar_color   = "#00e676" if floor_locked else "#6366f1"
    status_text = "FLOOR LOCKED" if floor_locked else f"${to_lock:,.2f} to lock"

    return (
        f"<div style='background:#08081a;border:1px solid #1e1e38;border-radius:10px;"
        f"padding:0.9rem 1rem;margin-top:0.8rem'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem'>"
        f"<span style='color:#8888bb;font-size:0.75rem;text-transform:uppercase;"
        f"letter-spacing:0.1em;font-weight:600'>Trailing MLL — ${trail_amt:,.0f} drawdown</span>"
        f"<span style='color:{mll_color};font-size:0.82rem;font-weight:700'>{status_text}</span>"
        f"</div>"
        f"<div style='height:8px;background:#13132a;border-radius:999px;overflow:hidden;margin-bottom:0.5rem'>"
        f"<div style='width:{trail_pct:.1f}%;height:8px;"
        f"background:linear-gradient(90deg,{bar_color}55,{bar_color});border-radius:999px'></div>"
        f"</div>"
        f"<div style='display:flex;gap:2rem;padding-top:0.5rem'>"
        f"<div><div style='color:#6666aa;font-size:0.75rem;margin-bottom:0.15rem'>MLL</div>"
        f"<div style='color:#f87171;font-size:0.95rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace'>${floor:,.0f}</div></div>"
        f"<div><div style='color:#6666aa;font-size:0.75rem;margin-bottom:0.15rem'>Balance</div>"
        f"<div style='color:#f0f0f8;font-size:0.95rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace'>${curr_bal:,.0f}</div></div>"
        f"<div><div style='color:#6666aa;font-size:0.75rem;margin-bottom:0.15rem'>Cushion</div>"
        f"<div style='color:#f0b429;font-size:0.95rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace'>${curr_bal - floor:,.2f}</div></div>"
        f"<div style='margin-left:auto;text-align:right'>"
        f"<div style='color:#6666aa;font-size:0.75rem;margin-bottom:0.15rem'>"
        f"{'Status' if floor_locked else 'To Lock'}</div>"
        f"<div style='color:{mll_color};font-size:0.95rem;font-weight:700;"
        f"font-family:JetBrains Mono,monospace'>"
        f"{'LOCKED ✓' if floor_locked else f'${to_lock:,.2f}'}</div></div>"
        f"</div>"
        f"</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────

def render_accounts():
    st.markdown("## Accounts")
    accounts = _load_accounts()

    if not accounts:
        _md("""
        <div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:10px;
                    padding:2rem;text-align:center;margin-bottom:1.5rem'>
          <div style='color:#8888aa;font-size:1rem;margin-bottom:0.4rem'>No accounts yet.</div>
          <div style='color:#44445a;font-size:0.88rem'>Add your first account using the form below.</div>
        </div>
        """)

    if accounts:
        active    = [a for a in accounts if a.get("status") == "active"]
        funded    = [a for a in accounts if a.get("type") == "funded" and a.get("status") == "active"]
        evals     = [a for a in accounts if a.get("type") == "eval" and a.get("status") == "active"]
        total_cap = sum(a.get("current_balance", a.get("starting_balance", 0)) for a in active)

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Active Accounts", len(active))
        s2.metric("Active Evals", len(evals))
        s3.metric("Funded Accounts", len(funded))
        s4.metric("Total Capital", f"${total_cap:,.0f}")
        st.divider()

    for acct in accounts:
        _render_account_card(acct, accounts)

    st.divider()
    with st.expander("➕  Add New Account", expanded=not accounts):
        _render_add_account_form(accounts)


# ─────────────────────────────────────────────────────────────────────────────

def _render_account_card(acct: dict, all_accounts: list[dict]):
    status    = acct.get("status", "active")
    acct_type = acct.get("type", "eval")
    challenge = acct.get("challenge_type", "n/a")
    fg, bg, status_label = _status_style(status)
    type_color = _type_color(acct_type)

    start_bal  = acct.get("starting_balance", 0)
    curr_bal   = acct.get("current_balance", start_bal)
    high_bal   = acct.get("highest_balance", max(curr_bal, start_bal))
    profit_tgt = acct.get("profit_target", 0)
    ddl        = acct.get("daily_loss_limit", 0)
    trail_amt  = acct.get("trailing_drawdown_amount", acct.get("max_trailing_drawdown", 1000))
    floor, _   = _calc_floor(acct)

    pnl         = curr_bal - start_bal
    pnl_pct     = (pnl / start_bal * 100) if start_bal else 0
    tgt_pct     = (pnl / profit_tgt * 100) if profit_tgt else 0
    tgt_clamped = min(tgt_pct, 100)
    pnl_color   = "#00e676" if pnl >= 0 else "#ff4444"
    cushion     = curr_bal - floor

    try:
        start = date.fromisoformat(acct.get("first_trade_date") or acct.get("start_date", str(date.today())))
        days  = (date.today() - start).days + 1
    except Exception:
        days = 0

    floor_cap    = acct.get("account_floor_cap", start_bal)
    floor_locked = bool(acct.get("trailing_drawdown") and (high_bal - trail_amt) >= floor_cap)
    floor_color  = "#00e676" if floor_locked else "#f87171"
    cushion_color = "#00e676" if cushion > ddl else "#f0b429"

    challenge_html = _challenge_badge(challenge, acct_type)
    platform_text  = f" · {acct.get('platform','')}" if acct.get("platform") else ""

    consist_active = acct.get("consistency_rule", False)
    consist_pct    = acct.get("consistency_rule_pct", 0)
    consist_html   = (
        f"<span style='background:#6366f122;color:#818cf8;padding:2px 8px;border-radius:6px;"
        f"font-size:0.75rem;font-weight:700;letter-spacing:0.06em'>CONSISTENCY {consist_pct:.0f}%</span>"
        if consist_active else ""
    )

    mll_html = (
        _mll_tracker_html(start_bal, curr_bal, high_bal, floor, floor_cap, trail_amt, floor_locked)
        if acct.get("trailing_drawdown") else ""
    )

    # ── Card (fully self-contained HTML) ──────────────────────────────────────
    _md(f"""
    <div style='background:#0c0c14;border:1px solid #1e1e38;border-radius:14px;
                padding:1.4rem 1.5rem;margin-bottom:0.4rem;position:relative;overflow:hidden'>
      <div style='position:absolute;top:0;left:0;right:0;height:3px;
                  background:linear-gradient(90deg,transparent,{type_color},transparent)'></div>
      <div style='display:flex;justify-content:space-between;align-items:center;
                  margin-bottom:1.1rem;flex-wrap:wrap;gap:0.5rem'>
        <div style='display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap'>
          <span style='background:{type_color}22;color:{type_color};padding:3px 10px;
                       border-radius:6px;font-size:0.8rem;font-weight:700;
                       text-transform:uppercase;letter-spacing:0.08em'>{acct_type}</span>
          {challenge_html}
          <span style='color:#f0f0f8;font-size:1.18rem;font-weight:700;margin-left:0.3rem'>{acct.get("label","—")}</span>
          <span style='color:#6666aa;font-size:0.92rem'>· {acct.get("firm","—")}{platform_text}</span>
        </div>
        <div style='display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap'>
          {consist_html}
          <span style='background:{bg};color:{fg};padding:3px 14px;border-radius:999px;
                       font-size:0.8rem;font-weight:700;letter-spacing:0.05em;white-space:nowrap'>{status_label}</span>
        </div>
      </div>
      <div style='display:grid;grid-template-columns:repeat(6,1fr);gap:1rem;margin-bottom:1.1rem'>
        <div style='background:#0a0a18;border-radius:10px;padding:0.8rem;border:1px solid #1a1a30'>
          <div style='color:#6666aa;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>Balance</div>
          <div style='color:#f0f0f8;font-size:1.25rem;font-weight:700;font-family:JetBrains Mono,monospace'>${curr_bal:,.2f}</div>
          <div style='color:{pnl_color};font-size:0.82rem;font-family:JetBrains Mono,monospace;margin-top:0.15rem'>{'+' if pnl >= 0 else ''}${pnl:,.2f} ({pnl_pct:+.1f}%)</div>
        </div>
        <div style='background:#0a0a18;border-radius:10px;padding:0.8rem;border:1px solid #1a1a30'>
          <div style='color:#6666aa;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>High Water</div>
          <div style='color:#f0f0f8;font-size:1.25rem;font-weight:700;font-family:JetBrains Mono,monospace'>${high_bal:,.2f}</div>
          <div style='color:#8888bb;font-size:0.82rem;margin-top:0.15rem'>peak balance</div>
        </div>
        <div style='background:#0a0a18;border-radius:10px;padding:0.8rem;border:1px solid #1a1a30'>
          <div style='color:#6666aa;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>Target</div>
          <div style='color:#f0b429;font-size:1.25rem;font-weight:700;font-family:JetBrains Mono,monospace'>${profit_tgt:,.0f}</div>
          <div style='color:#8888bb;font-size:0.82rem;margin-top:0.15rem'>${max(0, profit_tgt - pnl):,.2f} left</div>
        </div>
        <div style='background:#0a0a18;border-radius:10px;padding:0.8rem;border:1px solid #1a1a30'>
          <div style='color:#6666aa;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>Daily Stop</div>
          <div style='color:#ff6b6b;font-size:1.25rem;font-weight:700;font-family:JetBrains Mono,monospace'>${ddl:,.0f}</div>
          <div style='color:#8888bb;font-size:0.82rem;margin-top:0.15rem'>{acct.get("daily_loss_limit_pct",0):.0f}% / day</div>
        </div>
        <div style='background:#0a0a18;border-radius:10px;padding:0.8rem;border:1px solid #1a1a30'>
          <div style='color:#6666aa;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>DD Floor</div>
          <div style='color:{floor_color};font-size:1.25rem;font-weight:700;font-family:JetBrains Mono,monospace'>${floor:,.0f}</div>
          <div style='color:#8888bb;font-size:0.82rem;margin-top:0.15rem'>{"🔒 locked" if floor_locked else "trailing"}</div>
        </div>
        <div style='background:#0a0a18;border-radius:10px;padding:0.8rem;border:1px solid #1a1a30'>
          <div style='color:#6666aa;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>Cushion</div>
          <div style='color:{cushion_color};font-size:1.25rem;font-weight:700;font-family:JetBrains Mono,monospace'>${cushion:,.0f}</div>
          <div style='color:#8888bb;font-size:0.82rem;margin-top:0.15rem'>Day {days}</div>
        </div>
      </div>
      <div style='margin-bottom:0.6rem'>
        <div style='display:flex;justify-content:space-between;margin-bottom:0.35rem'>
          <span style='color:#8888bb;font-size:0.82rem;text-transform:uppercase;letter-spacing:0.07em'>Progress to Target</span>
          <span style='color:{"#00e676" if tgt_pct >= 100 else "#f0b429"};font-size:0.82rem;font-weight:700'>{tgt_pct:.1f}% · ${max(0, profit_tgt - pnl):,.2f} left</span>
        </div>
        <div style='background:#0d0d1f;border-radius:999px;height:7px'>
          <div style='background:linear-gradient(90deg,{"#00e676" if tgt_pct >= 100 else "#f0b429"}88,{"#00e676" if tgt_pct >= 100 else "#f0b429"});
                      width:{tgt_clamped:.1f}%;height:7px;border-radius:999px'></div>
        </div>
      </div>
      {mll_html}
    </div>
    """)

    # ── Rules & Notes expander ────────────────────────────────────────────────
    rules = acct.get("rules", [])
    notes = acct.get("notes", "")
    if rules or notes:
        with st.expander(f"📋  Rules & Notes ({len(rules)})", expanded=False):
            if notes:
                st.markdown(
                    f"<div style='background:#0d0d20;border-left:3px solid #f0b429;border-radius:0 8px 8px 0;"
                    f"padding:0.8rem 1rem;margin-bottom:0.8rem;color:#c8c8e8;"
                    f"font-size:0.92rem;line-height:1.6'>{notes}</div>",
                    unsafe_allow_html=True,
                )
            if rules:
                rows = "".join(
                    f"<div style='display:flex;align-items:flex-start;gap:0.6rem;padding:0.5rem 0;"
                    f"border-bottom:1px solid #16162a'>"
                    f"<span style='color:#f0b429;font-size:0.92rem;flex-shrink:0'>▸</span>"
                    f"<span style='color:#d0d0f0;font-size:0.92rem;line-height:1.5'>{rule}</span></div>"
                    for rule in rules
                )
                st.markdown(f"<div style='background:#08080f;border-radius:8px;padding:0 0.6rem'>{rows}</div>",
                             unsafe_allow_html=True)

    # ── Balance quick-update ──────────────────────────────────────────────────
    bc1, bc2, bc3 = st.columns([2, 2, 1])
    with bc1:
        new_bal = st.number_input("Current balance ($)", value=float(curr_bal), step=1.0,
                                   key=f"bal_{acct['id']}")
    with bc2:
        new_high = st.number_input("Highest balance ($)", value=float(high_bal), step=1.0,
                                    key=f"high_{acct['id']}",
                                    help="Highest this account has ever been. Floor trails from here.")
    with bc3:
        st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        if st.button("Save", key=f"save_{acct['id']}"):
            acct["current_balance"] = float(new_bal)
            acct["highest_balance"] = float(max(new_high, new_bal))
            _save_accounts(_replace_account(acct, all_accounts))
            st.rerun()

    # ── Edit / Delete buttons ─────────────────────────────────────────────────
    edit_key = f"editing_{acct['id']}"
    del_key  = f"del_confirm_{acct['id']}"

    _, btn_c2, btn_c3 = st.columns([4, 1, 1])
    with btn_c2:
        is_editing = st.session_state.get(edit_key, False)
        label = "✕  Close Edit" if is_editing else "✏  Edit"
        if st.button(label, key=f"editbtn_{acct['id']}", use_container_width=True):
            st.session_state[edit_key] = not is_editing
            st.session_state.pop(del_key, None)
            st.rerun()
    with btn_c3:
        if not st.session_state.get(del_key, False):
            if st.button("🗑  Delete", key=f"delbtn_{acct['id']}", use_container_width=True):
                st.session_state[del_key] = True
                st.rerun()
        else:
            if st.button("⚠ Confirm?", key=f"delconfirm_{acct['id']}", use_container_width=True, type="primary"):
                updated_list = [a for a in all_accounts if a["id"] != acct["id"]]
                _save_accounts(updated_list)
                st.session_state.pop(del_key, None)
                st.session_state.pop(edit_key, None)
                st.rerun()

    # ── Inline edit form ──────────────────────────────────────────────────────
    if st.session_state.get(edit_key, False):
        _render_edit_form(acct, all_accounts)

    st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────

def _render_edit_form(acct: dict, all_accounts: list[dict]):
    st.markdown(
        "<div style='color:#f0b429;font-size:0.82rem;text-transform:uppercase;"
        "letter-spacing:0.1em;font-weight:700;margin:0.5rem 0'>✏  Edit Account</div>",
        unsafe_allow_html=True,
    )

    with st.form(f"edit_form_{acct['id']}"):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**Identity**")
            new_label     = st.text_input("Label", value=acct.get("label", ""))
            new_firm      = st.text_input("Firm", value=acct.get("firm", ""))
            new_type      = st.selectbox("Type", ACCOUNT_TYPES,
                                          index=_idx(ACCOUNT_TYPES, acct.get("type", "eval")))
            new_challenge = st.selectbox("Challenge Type", CHALLENGE_TYPES,
                                          index=_idx(CHALLENGE_TYPES, acct.get("challenge_type", "n/a")))
            new_status    = st.selectbox("Status", STATUSES,
                                          index=_idx(STATUSES, acct.get("status", "active")))
            new_asset     = st.selectbox("Asset Class", ASSET_CLASSES,
                                          index=_idx(ASSET_CLASSES, acct.get("asset_class", "Futures")))
            new_platform  = st.selectbox("Platform", PLATFORMS,
                                          index=_idx(PLATFORMS, acct.get("platform", "Tradovate")))

        with c2:
            st.markdown("**Balances & Dates**")
            new_start_bal = st.number_input("Starting Balance ($)", value=float(acct.get("starting_balance", 25000)), step=100.0)
            new_curr_bal  = st.number_input("Current Balance ($)",  value=float(acct.get("current_balance", 25000)), step=1.0)
            new_high_bal  = st.number_input("Highest Balance ($)",  value=float(acct.get("highest_balance", 25000)), step=1.0)
            new_start_date  = st.date_input("Start Date",       value=_parse_date(acct.get("start_date")))
            new_first_trade = st.date_input("First Trade Date", value=_parse_date(acct.get("first_trade_date")))
            new_payout    = st.number_input("Payout Split (%)", value=float(acct.get("payout_split", 80)), min_value=0.0, max_value=100.0, step=5.0)

        with c3:
            st.markdown("**Limits & Rules**")
            new_profit_tgt = st.number_input("Profit Target ($)",       value=float(acct.get("profit_target", 0)), step=100.0)
            new_ddl        = st.number_input("Daily Loss Limit ($)",    value=float(acct.get("daily_loss_limit", 0)), step=50.0)
            new_trailing   = st.checkbox("Trailing Drawdown",           value=acct.get("trailing_drawdown", False))
            new_trail_amt  = st.number_input("Trailing DD Amount ($)",  value=float(acct.get("trailing_drawdown_amount", acct.get("max_trailing_drawdown", 1000))), step=50.0)
            new_floor_cap  = st.number_input("Floor Cap ($)",           value=float(acct.get("account_floor_cap", acct.get("starting_balance", 25000))), step=100.0)
            new_min_days      = st.number_input("Min Trading Days",        value=int(acct.get("min_trading_days", 0)), min_value=0, step=1)
            new_consistency   = st.checkbox("Consistency Rule",         value=acct.get("consistency_rule", False))
            new_consist_pct   = st.number_input("Consistency % (if enabled)", value=float(acct.get("consistency_rule_pct", 30.0)),
                                                 min_value=0.0, max_value=100.0, step=1.0,
                                                 help="Max % any single day can be of total profit. Only applies if Consistency Rule is checked.")
            new_news       = st.checkbox("News Trading Allowed",        value=acct.get("news_trading", True))
            new_weekend    = st.checkbox("Weekend Holding Allowed",     value=acct.get("weekend_holding", False))

        new_symbols = st.text_input("Symbols (comma-separated)", value=", ".join(acct.get("symbols", [])))
        new_rules   = st.text_area("Rules (one per line)", height=120, value="\n".join(acct.get("rules", [])))
        new_notes   = st.text_area("Notes", height=80, value=acct.get("notes", ""))

        save_c, cancel_c = st.columns(2)
        with save_c:
            saved = st.form_submit_button("Save Changes", use_container_width=True, type="primary")
        with cancel_c:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if saved:
            sym_list   = [s.strip() for s in new_symbols.split(",") if s.strip()]
            rules_list = [r.strip() for r in new_rules.splitlines() if r.strip()]
            updated = dict(acct)
            updated.update({
                "label":                    new_label,
                "firm":                     new_firm,
                "type":                     new_type,
                "challenge_type":           new_challenge,
                "status":                   new_status,
                "asset_class":              new_asset,
                "platform":                 new_platform,
                "starting_balance":         float(new_start_bal),
                "current_balance":          float(new_curr_bal),
                "highest_balance":          float(max(new_high_bal, new_curr_bal)),
                "start_date":               str(new_start_date),
                "first_trade_date":         str(new_first_trade),
                "payout_split":             float(new_payout),
                "profit_target":            float(new_profit_tgt),
                "profit_target_pct":        round(new_profit_tgt / new_start_bal * 100, 1) if new_start_bal else 0,
                "daily_loss_limit":         float(new_ddl),
                "daily_loss_limit_pct":     round(new_ddl / new_start_bal * 100, 1) if new_start_bal else 0,
                "trailing_drawdown":        new_trailing,
                "trailing_drawdown_amount": float(new_trail_amt),
                "max_trailing_drawdown":    float(new_trail_amt),
                "account_floor_cap":        float(new_floor_cap),
                "min_trading_days":         int(new_min_days),
                "consistency_rule":         new_consistency,
                "consistency_rule_pct":     float(new_consist_pct) if new_consistency else 0.0,
                "news_trading":             new_news,
                "weekend_holding":          new_weekend,
                "symbols":                  sym_list,
                "rules":                    rules_list,
                "notes":                    new_notes,
            })
            _save_accounts(_replace_account(updated, all_accounts))
            st.session_state.pop(f"editing_{acct['id']}", None)
            st.success("Account updated.")
            st.rerun()

        if cancelled:
            st.session_state.pop(f"editing_{acct['id']}", None)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────

def _render_add_account_form(existing: list[dict]):
    with st.form("add_account", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**Identity**")
            label       = st.text_input("Account Label", placeholder="e.g. Apex 50K Eval #1")
            firm_preset = st.selectbox("Firm", FIRMS_PRESETS)
            firm_other  = st.text_input("Firm name (if 'Other')", placeholder="Custom firm")
            acct_type   = st.selectbox("Type", ACCOUNT_TYPES)
            challenge   = st.selectbox("Challenge Type", CHALLENGE_TYPES)
            asset_class = st.selectbox("Asset Class", ASSET_CLASSES)
            platform    = st.selectbox("Platform", PLATFORMS)
            symbols     = st.text_input("Symbols (comma-sep)", placeholder="MES, MNQ, ES")

        with c2:
            st.markdown("**Balances & Dates**")
            start_bal   = st.number_input("Starting Balance ($)", min_value=0.0, step=100.0, value=25000.0)
            profit_tgt  = st.number_input("Profit Target ($)",    min_value=0.0, step=100.0)
            ddl         = st.number_input("Daily Loss Limit ($)", min_value=0.0, step=50.0)
            start_date  = st.date_input("Start Date")
            first_trade = st.date_input("First Trade Date")
            payout      = st.number_input("Payout Split (%)", value=80.0, min_value=0.0, max_value=100.0, step=5.0)

        with c3:
            st.markdown("**Drawdown & Rules**")
            trailing    = st.checkbox("Trailing Drawdown", value=True)
            trail_amt   = st.number_input("Trailing DD Amount ($)", min_value=0.0, step=50.0, value=1000.0)
            floor_cap   = st.number_input("Floor Cap ($)",          min_value=0.0, step=100.0, value=25000.0)
            min_days      = st.number_input("Min Trading Days",       value=0, min_value=0, step=1)
            consistency   = st.checkbox("Consistency Rule")
            consist_pct   = st.number_input("Consistency % (if enabled)", value=30.0,
                                             min_value=0.0, max_value=100.0, step=1.0,
                                             help="Max % any single day can be of total profit. Only applies if Consistency Rule is checked.")
            news_ok     = st.checkbox("News Trading Allowed",       value=True)
            weekend_ok  = st.checkbox("Weekend Holding Allowed",    value=False)

        rules_raw = st.text_area("Rules (one per line)", height=100,
                                  placeholder="Daily loss limit: $1,000 hard stop\nNo overnight positions")
        notes     = st.text_area("Notes", height=60)

        if st.form_submit_button("Add Account", use_container_width=True, type="primary"):
            firm = firm_other.strip() if firm_preset == "Other" and firm_other.strip() else firm_preset
            if not label.strip() or not firm:
                st.error("Label and Firm are required.")
                return

            account_id = re.sub(r"[^a-z0-9]", "_", label.lower())[:30]
            sym_list   = [s.strip() for s in symbols.split(",") if s.strip()]
            rules_list = [r.strip() for r in rules_raw.splitlines() if r.strip()]

            new_acct = {
                "id":                         account_id,
                "label":                      label.strip(),
                "firm":                       firm,
                "type":                       acct_type,
                "challenge_type":             challenge,
                "status":                     "active",
                "asset_class":                asset_class,
                "platform":                   platform,
                "symbols":                    sym_list,
                "start_date":                 str(start_date),
                "first_trade_date":           str(first_trade),
                "starting_balance":           float(start_bal),
                "current_balance":            float(start_bal),
                "highest_balance":            float(start_bal),
                "profit_target":              float(profit_tgt),
                "profit_target_pct":          round(profit_tgt / start_bal * 100, 1) if start_bal else 0,
                "daily_loss_limit":           float(ddl),
                "daily_loss_limit_pct":       round(ddl / start_bal * 100, 1) if start_bal else 0,
                "trailing_drawdown":          trailing,
                "trailing_drawdown_amount":   float(trail_amt),
                "max_trailing_drawdown":      float(trail_amt),
                "max_trailing_drawdown_pct":  round(trail_amt / start_bal * 100, 1) if start_bal else 0,
                "account_floor_cap":          float(floor_cap),
                "payout_split":               float(payout),
                "min_trading_days":           int(min_days),
                "consistency_rule":           consistency,
                "consistency_rule_pct":       float(consist_pct) if consistency else 0.0,
                "news_trading":               news_ok,
                "weekend_holding":            weekend_ok,
                "rules":                      rules_list,
                "notes":                      notes.strip(),
            }
            _save_accounts(existing + [new_acct])
            st.success(f"Account '{label}' added.")
            st.rerun()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _idx(lst: list, val: str) -> int:
    try:
        return lst.index(val)
    except ValueError:
        return 0


def _parse_date(s: str | None) -> date:
    try:
        return date.fromisoformat(s) if s else date.today()
    except Exception:
        return date.today()

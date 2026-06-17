"""
Tradovate API client — read-only trade tracking.
Pulls fills, positions, and account metrics from Tradovate REST API.
Real credentials go in config/config.env (TRADOVATE_USERNAME, PASSWORD, CID, SECRET, MODE).
"""
import os
import time
import requests
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "config" / "config.env")

_MODE     = os.getenv("TRADOVATE_MODE", "demo").lower()
_USERNAME = os.getenv("TRADOVATE_USERNAME", "")
_PASSWORD = os.getenv("TRADOVATE_PASSWORD", "")
_CID      = os.getenv("TRADOVATE_CID", "")
_SECRET   = os.getenv("TRADOVATE_SECRET", "")

_BASE_URLS = {
    "demo": "https://demo.tradovateapi.com/v1",
    "live": "https://live.tradovateapi.com/v1",
}
_BASE = _BASE_URLS.get(_MODE, _BASE_URLS["demo"])

_CREDENTIALS_SET = all([
    _USERNAME and _USERNAME != "your_email@example.com",
    _PASSWORD and _PASSWORD != "your_password",
    _CID and _CID != "your_client_id_number",
    _SECRET and _SECRET != "your_client_secret",
])

# ── Token cache (module-level, lives for the session) ──────────────────────
_token_cache: dict = {"token": None, "expiry": 0}


def _get_token() -> str | None:
    """Get or refresh OAuth access token."""
    if not _CREDENTIALS_SET:
        return None

    now = time.time()
    if _token_cache["token"] and now < _token_cache["expiry"] - 60:
        return _token_cache["token"]

    try:
        resp = requests.post(
            f"{_BASE}/auth/oauthtoken",
            json={
                "name":     _USERNAME,
                "password": _PASSWORD,
                "appId":    "JarvisDashboard",
                "appVersion": "1.0",
                "cid":      int(_CID),
                "sec":      _SECRET,
                "deviceId": "jarvis-win11",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            _token_cache["token"]  = data.get("accessToken")
            expires_in             = data.get("expirationTime", 3600)
            _token_cache["expiry"] = now + expires_in
            return _token_cache["token"]
        return None
    except Exception:
        return None


def _get(endpoint: str) -> dict | list | None:
    """Authenticated GET helper."""
    token = _get_token()
    if not token:
        return None
    try:
        resp = requests.get(
            f"{_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


# ── Public API ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_account_status() -> dict:
    """
    Returns live account metrics for the sidebar.
    Returns {"connected": False} if credentials not set or API unreachable.
    """
    if not _CREDENTIALS_SET:
        return {"connected": False, "reason": "credentials_not_set"}

    accounts = _get("/account/list")
    if not accounts:
        return {"connected": False, "reason": "auth_failed"}

    acct = accounts[0] if isinstance(accounts, list) else accounts

    # Balance snapshot
    acct_id = acct.get("id")
    balance_data = _get(f"/cashBalance/getCashBalanceSnapshot?accountId={acct_id}")
    balance = 0.0
    if balance_data and isinstance(balance_data, list) and balance_data:
        balance = balance_data[0].get("totalCashValue", 0.0)
    elif isinstance(balance_data, dict):
        balance = balance_data.get("totalCashValue", 0.0)

    # Open positions
    positions = _get("/position/list") or []
    open_positions = [p for p in positions if p.get("netPos", 0) != 0 and p.get("accountId") == acct_id]

    # Today's fills
    daily_pnl = _get_daily_pnl(acct_id)

    return {
        "connected":       True,
        "name":            acct.get("name", "—"),
        "id":              acct_id,
        "balance":         balance,
        "daily_pnl":       daily_pnl,
        "open_positions":  open_positions,
        "mode":            _MODE,
    }


@st.cache_data(ttl=30)
def get_live_positions() -> list[dict]:
    """All open positions with current P&L."""
    if not _CREDENTIALS_SET:
        return []

    positions = _get("/position/list") or []
    return [p for p in positions if p.get("netPos", 0) != 0]


@st.cache_data(ttl=60)
def get_fills(days: int = 30) -> list[dict]:
    """
    Completed fills (trades) from Tradovate, most recent first.
    Each fill: symbol, side (Buy/Sell), qty, price, timestamp, orderId, fillId.
    """
    if not _CREDENTIALS_SET:
        return []

    fills = _get("/fill/list") or []
    if not isinstance(fills, list):
        return []

    # Filter to last N days
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    result = []
    for f in fills:
        ts_str = f.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            if ts < cutoff:
                continue
        except Exception:
            pass

        result.append({
            "fill_id":    f.get("id"),
            "order_id":   f.get("orderId"),
            "symbol":     f.get("contractId", {}).get("name", "—") if isinstance(f.get("contractId"), dict) else str(f.get("contractId", "—")),
            "side":       f.get("action", "—"),
            "qty":        f.get("qty", 0),
            "price":      f.get("price", 0.0),
            "timestamp":  ts_str,
            "commission": f.get("commission", 0.0),
        })

    result.sort(key=lambda x: x["timestamp"], reverse=True)
    return result


@st.cache_data(ttl=30)
def get_open_orders() -> list[dict]:
    """Orders that are working (not yet filled)."""
    if not _CREDENTIALS_SET:
        return []

    orders = _get("/order/list") or []
    return [o for o in orders if o.get("ordStatus") in ("Working", "Accepted", "PendingNew")]


def _get_daily_pnl(acct_id: int) -> float:
    """Sum today's closed P&L from fills (approximate via fill prices)."""
    try:
        fills = get_fills(1)
        today = datetime.now(timezone.utc).date().isoformat()
        total = sum(
            f.get("pnl", 0.0)
            for f in fills
            if f.get("timestamp", "")[:10] == today
        )
        return total
    except Exception:
        return 0.0


def credentials_status() -> dict:
    """Return human-readable credential status for the UI."""
    return {
        "set":  _CREDENTIALS_SET,
        "mode": _MODE,
        "user": _USERNAME[:4] + "***" if _CREDENTIALS_SET and _USERNAME else "not set",
        "cid":  _CID if _CREDENTIALS_SET else "not set",
    }

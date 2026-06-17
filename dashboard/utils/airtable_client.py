import os
import requests
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "config" / "config.env")


def _secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


_API_KEY = _secret("AIRTABLE_API_KEY")
_BASE_ID = _secret("AIRTABLE_BASE_ID", "appg72lUB8VIEKWy4")
_BASE_URL = f"https://api.airtable.com/v0/{_BASE_ID}"

_TABLES = {
    "trades":        "tblQx04ovCVqlE3va",
    "daily_summary": "tblNwbrJMSIL8hJb9",
    "pattern_flags": "tblZG4C8mmH4kN4BH",
}


def _headers():
    return {"Authorization": f"Bearer {_API_KEY}"}


def _extract(record: dict, key: str):
    val = record.get("fields", {}).get(key)
    if isinstance(val, dict) and "name" in val:
        return val["name"]
    if isinstance(val, list) and val and isinstance(val[0], dict):
        return ", ".join(v.get("name", str(v)) for v in val)
    return val


def _fetch_all(table_key: str, params: dict | None = None) -> list:
    url = f"{_BASE_URL}/{_TABLES[table_key]}"
    records, offset = [], None
    while True:
        p = dict(params or {})
        if offset:
            p["offset"] = offset
        try:
            r = requests.get(url, headers=_headers(), params=p, timeout=10)
            if r.status_code != 200:
                return records
            data = r.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
        except Exception:
            break
    return records


_last_post_error: str = ""


def _post(table_key: str, fields: dict) -> bool:
    global _last_post_error
    url = f"{_BASE_URL}/{_TABLES[table_key]}"
    try:
        r = requests.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json={"fields": fields},
            timeout=10,
        )
        if r.status_code in (200, 201):
            st.cache_data.clear()
            _last_post_error = ""
            return True
        try:
            err_body = r.json()
            err_type = err_body.get("error", {}).get("type", "")
            err_msg  = err_body.get("error", {}).get("message", r.text[:300])
        except Exception:
            err_type, err_msg = "", r.text[:300]
        _last_post_error = f"HTTP {r.status_code} ({err_type}): {err_msg}"
        return False
    except Exception as e:
        _last_post_error = str(e)
        return False


def get_last_post_error() -> str:
    return _last_post_error


@st.cache_data(ttl=60)
def get_trades(days: int = 30) -> list[dict]:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "filterByFormula": f"IS_AFTER({{Date}}, '{cutoff}')",
        "sort[0][field]": "Date",
        "sort[0][direction]": "desc",
    }
    return [
        {
            "id": r["id"],
            "trade_id": _extract(r, "Trade ID"),
            "date": _extract(r, "Date"),
            "symbol": _extract(r, "Symbol"),
            "direction": _extract(r, "Direction"),
            "entry": _extract(r, "Entry Price"),
            "exit": _extract(r, "Exit Price"),
            "contracts": _extract(r, "Contracts"),
            "pnl": _extract(r, "PnL ($)") or 0,
            "duration": _extract(r, "Duration (min)"),
            "session": _extract(r, "Session"),
            "setup_tags": _extract(r, "Setup Tags"),
            "rule_score": _extract(r, "Rule Score (0-8)"),
            "ddl_status": _extract(r, "DDL Status"),
            "rule_adherence": _extract(r, "Rule Adherence"),
            "result": _extract(r, "Result"),
            "notes": _extract(r, "Notes"),
        }
        for r in _fetch_all("trades", params)
    ]


@st.cache_data(ttl=60)
def get_daily_summaries(limit: int = 7) -> list[dict]:
    params = {
        "sort[0][field]": "Date",
        "sort[0][direction]": "desc",
        "maxRecords": str(limit),
    }
    return [
        {
            "id": r["id"],
            "date": _extract(r, "Date"),
            "pnl": _extract(r, "Total PnL ($)") or 0,
            "trades": _extract(r, "Trades Taken") or 0,
            "wins": _extract(r, "Wins") or 0,
            "losses": _extract(r, "Losses") or 0,
            "win_rate": _extract(r, "Win Rate (%)") or 0,
            "eval_balance": _extract(r, "Eval Balance ($)") or 0,
            "ddl_hit": _extract(r, "DDL Hit") or False,
            "closed_at_ddl": _extract(r, "Closed at DDL") or False,
            "day_grade": _extract(r, "Day Grade"),
            "coach_notes": _extract(r, "Coach Notes"),
        }
        for r in _fetch_all("daily_summary", params)
    ]


@st.cache_data(ttl=120)
def get_pattern_flags() -> list[dict]:
    return [
        {
            "flag": _extract(r, "Flag"),
            "date": _extract(r, "Date"),
            "pattern": _extract(r, "Pattern"),
            "severity": _extract(r, "Severity"),
            "occurrences": _extract(r, "Occurrences This Week") or 0,
            "note": _extract(r, "Coach Note"),
        }
        for r in _fetch_all("pattern_flags")
    ]


def create_trade(fields: dict) -> bool:
    return _post("trades", fields)


def create_daily_summary(fields: dict) -> bool:
    return _post("daily_summary", fields)

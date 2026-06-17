"""
Tradovate CSV/PDF trade report importer.
Handles two Tradovate export formats:
  1. Performance CSV  — round-trip trades (symbol, qty, buyPrice, sellPrice, pnl, timestamps)
  2. Account Statement CSV — fill-by-fill (tradeTime, action, price, commission)
"""
import io
import re
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path


def _parse_pnl(raw: str) -> float:
    """Convert Tradovate PnL string like '$780.00' or '$(224.00)' to float."""
    raw = str(raw).strip()
    negative = "(" in raw
    cleaned = re.sub(r"[$(),\s]", "", raw)
    try:
        val = float(cleaned)
        return -val if negative else val
    except Exception:
        return 0.0


def parse_performance_csv(file_content: bytes | str) -> list[dict]:
    """
    Parse Tradovate Performance CSV (Account → Reports → Performance).
    Columns: symbol, qty, buyPrice, sellPrice, pnl, boughtTimestamp, soldTimestamp, duration
    Returns round-trip trade records.
    """
    if isinstance(file_content, bytes):
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")
    else:
        text = file_content

    df = pd.read_csv(io.StringIO(text.strip()), dtype=str)
    df.columns = [c.strip() for c in df.columns]

    trades = []
    for _, row in df.iterrows():
        try:
            symbol_raw = str(row.get("symbol", "")).strip()
            if not symbol_raw or symbol_raw.lower() == "nan":
                continue

            symbol   = _clean_symbol(symbol_raw)
            qty      = int(float(str(row.get("qty", "1")).replace(",", "") or "1"))
            buy_p    = float(str(row.get("buyPrice", "0")).replace(",", "") or "0")
            sell_p   = float(str(row.get("sellPrice", "0")).replace(",", "") or "0")
            pnl      = _parse_pnl(row.get("pnl", "0"))
            buy_ts   = str(row.get("boughtTimestamp", "")).strip()
            sell_ts  = str(row.get("soldTimestamp", "")).strip()
            duration = str(row.get("duration", "")).strip()

            # Use earlier timestamp as trade date
            ts = buy_ts if buy_ts else sell_ts
            try:
                dt = datetime.strptime(ts, "%m/%d/%Y %H:%M:%S")
                date_str = dt.date().isoformat()
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                date_str = ts[:10] if ts else ""
                time_str = ""

            # Determine direction — if buyPrice came first, it was a Long
            direction = "Long"  # Performance CSV shows buy entry → sell exit for longs
            # If you shorted: sellPrice would be the entry, buyPrice the exit
            # Tradovate encodes: buyPrice = entry for long, or cover price for short
            # We'll use net PnL to verify
            if buy_p > 0 and sell_p > 0:
                if sell_p > buy_p:
                    direction = "Long"
                elif buy_p > sell_p:
                    direction = "Short"

            result = "Win" if pnl > 0 else ("Loss" if pnl < 0 else "Breakeven")
            session = _detect_session_from_str(ts)

            # Parse duration to minutes
            dur_min = 0
            m = re.search(r"(\d+)min", duration)
            if m:
                dur_min = int(m.group(1))

            trades.append({
                "timestamp":   buy_ts,
                "date":        date_str,
                "time":        time_str,
                "symbol":      symbol,
                "symbol_full": symbol_raw,
                "direction":   direction,
                "qty":         qty,
                "entry_price": buy_p if direction == "Long" else sell_p,
                "exit_price":  sell_p if direction == "Long" else buy_p,
                "pnl":         pnl,
                "duration_min": dur_min,
                "result":      result,
                "session":     session,
                "buy_fill_id": str(row.get("buyFillId", "")),
                "sell_fill_id": str(row.get("sellFillId", "")),
                "source":      "Tradovate Performance CSV",
            })
        except Exception:
            continue

    trades.sort(key=lambda x: x["timestamp"], reverse=True)
    return trades


# Tradovate CSV column name variations (they change slightly between report types)
_COL_MAP = {
    # Tradovate column → our field
    "tradeTime":        "timestamp",
    "TradeTime":        "timestamp",
    "fillTime":         "timestamp",
    "FillTime":         "timestamp",
    "contractName":     "symbol",
    "ContractName":     "symbol",
    "contract":         "symbol",
    "Contract":         "symbol",
    "symbol":           "symbol",
    "Symbol":           "symbol",
    "action":           "side",
    "Action":           "side",
    "side":             "side",
    "Side":             "side",
    "qty":              "qty",
    "Qty":              "qty",
    "quantity":         "qty",
    "Quantity":         "qty",
    "price":            "price",
    "Price":            "price",
    "fillPrice":        "price",
    "FillPrice":        "price",
    "commission":       "commission",
    "Commission":       "commission",
    "realizedPnl":      "pnl",
    "RealizedPnl":      "pnl",
    "netPnl":           "pnl",
    "NetPnl":           "pnl",
    "tradePnl":         "pnl",
    "TradePnl":         "pnl",
    "orderId":          "order_id",
    "OrderId":          "order_id",
    "fillId":           "fill_id",
    "FillId":           "fill_id",
    "accountName":      "account",
    "AccountName":      "account",
}

_SESSION_MAP = [
    (range(8, 12),  "NY"),
    (range(14, 17), "After Hours"),
    (range(2, 7),   "London"),
    (range(18, 24), "Asia"),
    (range(0, 2),   "Asia"),
]


def _detect_session(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        hour = dt.astimezone().hour
        for h_range, session in _SESSION_MAP:
            if hour in h_range:
                return session
    except Exception:
        pass
    return "NY"


def _detect_session_from_str(ts_str: str) -> str:
    """Handle Tradovate's MM/DD/YYYY HH:MM:SS format."""
    try:
        dt = datetime.strptime(ts_str, "%m/%d/%Y %H:%M:%S")
        hour = dt.hour
        for h_range, session in _SESSION_MAP:
            if hour in h_range:
                return session
    except Exception:
        return _detect_session(ts_str)
    return "NY"


def _clean_symbol(raw: str) -> str:
    """Convert Tradovate contract name (e.g. MESM5) → base symbol (MES)."""
    raw = str(raw).strip().upper()
    # Strip month/year suffix: M5, Z4, H5, U5, etc.
    cleaned = re.sub(r"[FGHJKMNQUVXZ]\d{1,2}$", "", raw)
    return cleaned or raw


def parse_tradovate_csv(file_content: bytes | str) -> list[dict]:
    """Auto-detect Tradovate CSV format and parse accordingly."""
    if isinstance(file_content, bytes):
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")
    else:
        text = file_content

    first_line = text.strip().split("\n")[0].lower()
    # Performance CSV has these columns
    if "buyprice" in first_line or "soldtimestamp" in first_line or "boughttimestamp" in first_line:
        return parse_performance_csv(text)
    # Otherwise fall through to account statement parser
    return _parse_account_statement_csv(text)


def _parse_account_statement_csv(text: str) -> list[dict]:
    """
    Parse a Tradovate Account Report CSV.
    Returns a list of trade dicts ready for Airtable / display.
    """

    # Skip any header lines before the actual CSV
    lines = text.strip().split("\n")
    csv_start = 0
    for i, line in enumerate(lines):
        if "," in line and len(line.split(",")) >= 4:
            csv_start = i
            break

    csv_text = "\n".join(lines[csv_start:])
    df = pd.read_csv(io.StringIO(csv_text), dtype=str)

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    rename = {col: _COL_MAP[col] for col in df.columns if col in _COL_MAP}
    df = df.rename(columns=rename)

    trades = []
    for _, row in df.iterrows():
        try:
            symbol_raw = str(row.get("symbol", "")).strip()
            if not symbol_raw or symbol_raw.lower() in ("nan", ""):
                continue

            symbol  = _clean_symbol(symbol_raw)
            ts_raw  = str(row.get("timestamp", "")).strip()
            side    = str(row.get("side", "")).strip()
            qty_str = str(row.get("qty", "0")).replace(",", "")
            qty     = int(float(qty_str)) if qty_str else 0

            price_str = str(row.get("price", "0")).replace(",", "").replace("$", "")
            price = float(price_str) if price_str and price_str != "nan" else 0.0

            pnl_str = str(row.get("pnl", "0")).replace(",", "").replace("$", "")
            pnl = float(pnl_str) if pnl_str and pnl_str not in ("nan", "") else None

            comm_str = str(row.get("commission", "0")).replace(",", "").replace("$", "")
            commission = float(comm_str) if comm_str and comm_str != "nan" else 0.0

            session = _detect_session(ts_raw)

            # Format timestamp for display
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                date_str = dt.date().isoformat()
                time_str = dt.astimezone().strftime("%H:%M:%S")
            except Exception:
                date_str = ts_raw[:10] if ts_raw else ""
                time_str = ""

            trades.append({
                "timestamp":    ts_raw,
                "date":         date_str,
                "time":         time_str,
                "symbol":       symbol,
                "symbol_full":  symbol_raw,
                "side":         side,
                "direction":    "Long" if side.lower() in ("buy", "long") else "Short",
                "qty":          qty,
                "price":        price,
                "pnl":          pnl,
                "commission":   commission,
                "session":      session,
                "order_id":     str(row.get("order_id", "")),
                "fill_id":      str(row.get("fill_id", "")),
                "account":      str(row.get("account", "")),
                "source":       "Tradovate CSV",
            })
        except Exception:
            continue

    # Sort most recent first
    trades.sort(key=lambda x: x["timestamp"], reverse=True)
    return trades


def parse_tradovate_pdf(file_content: bytes) -> list[dict]:
    """Extract trade data from Tradovate PDF report (uses pdfplumber)."""
    try:
        import pdfplumber, io
        rows = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    rows.extend(table)

        if not rows:
            return []

        # First row is headers
        headers = [str(h).strip() if h else "" for h in rows[0]]
        trades_raw = []
        for row in rows[1:]:
            if row and any(cell for cell in row):
                record = {headers[i]: str(cell).strip() if cell else "" for i, cell in enumerate(row) if i < len(headers)}
                trades_raw.append(record)

        # Convert to CSV-like format and reuse CSV parser
        if trades_raw:
            import csv, io as sio
            buf = sio.StringIO()
            writer = csv.DictWriter(buf, fieldnames=headers)
            writer.writeheader()
            writer.writerows(trades_raw)
            return parse_tradovate_csv(buf.getvalue())

    except Exception as e:
        return []

    return []


_RESULT_MAP = {"Win": "Win", "Loss": "Loss", "Breakeven": "BE", "BE": "BE"}
_SESSION_VALID = {"NY", "London", "NY-London Overlap", "Asia", "After Hours"}


def fills_to_airtable_fields(fill: dict, rule_score: int | None = None, result: str | None = None) -> dict:
    """Convert a parsed trade/fill to Airtable field format."""
    pnl = fill.get("pnl") or 0.0

    # Auto-determine result from PnL if not overridden
    if result is None:
        result = fill.get("result") or ("Win" if pnl > 0 else ("Loss" if pnl < 0 else "BE"))
    result = _RESULT_MAP.get(result, "BE")

    trade_id = (
        f"TV_{fill.get('buy_fill_id','') or fill.get('fill_id','') or fill.get('order_id','') or fill.get('timestamp','')[:16].replace(' ','T').replace(':','')}"
    )

    entry  = fill.get("entry_price") or fill.get("price") or 0.0
    exit_p = fill.get("exit_price") or 0.0
    dur    = fill.get("duration_min") or 0

    notes_parts = [f"Imported from Tradovate ({fill.get('source','CSV')})."]
    notes_parts.append(f"Entry: {entry:.4f} → Exit: {exit_p:.4f}")
    notes_parts.append(f"×{fill.get('qty',1)} contracts")
    if fill.get("commission"):
        notes_parts.append(f"Commission: ${fill.get('commission',0):.2f}")

    session_raw = fill.get("session", "NY")
    session = session_raw if session_raw in _SESSION_VALID else "NY"

    return {
        "Trade ID":           trade_id,
        "Date":               fill["date"] + "T00:00:00.000Z" if fill.get("date") else "",
        "Symbol":             fill.get("symbol", ""),
        "Direction":          fill.get("direction", "Long"),
        "Entry Price":        float(entry),
        "Exit Price":         float(exit_p),
        "Contracts":          int(fill.get("qty", 1)),
        "PnL ($)":            float(pnl),
        "Duration (min)":     int(dur),
        "Session":            session,
        "Result":             result,
        "Source":             "Tradovate Performance CSV",
        "Notes":              " ".join(notes_parts),
        **({"Rule Score (0-8)": rule_score} if rule_score is not None else {}),
    }

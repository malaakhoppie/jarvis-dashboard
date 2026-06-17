"""
Market data, session clock, and news feeds for the Markets tab.
Uses yfinance for prices and RSS for headlines — no paid API required.
"""
import os
import json
import requests
import streamlit as st
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent.parent.parent

EST = ZoneInfo("America/New_York")

# ── Instruments ───────────────────────────────────────────────────────────────
INSTRUMENTS = [
    ("GC=F",  "Gold",        "GC",  "#f0b429"),
    ("MGC=F", "Micro Gold",  "MGC", "#f0b429"),
    ("ES=F",  "E-Mini S&P",  "ES",  "#00d4ff"),
    ("MES=F", "Micro S&P",   "MES", "#00d4ff"),
    ("NQ=F",  "Nasdaq 100",  "NQ",  "#a78bfa"),
    ("MNQ=F", "Micro NQ",    "MNQ", "#a78bfa"),
    ("YM=F",  "Dow Jones",   "YM",  "#34d399"),
    ("CL=F",  "Crude Oil",   "CL",  "#fb923c"),
]

# ── Session windows (EST) ─────────────────────────────────────────────────────
SESSIONS = [
    ("Asia",     (20, 0), (4,  0), "#a78bfa"),
    ("London",   (3,  0), (12, 0), "#00d4ff"),
    ("New York", (8,  0), (16, 0), "#00e676"),
]


def get_session_info() -> dict:
    """Return current session name, color, minutes remaining, and next session."""
    now = datetime.now(EST)
    mins = now.hour * 60 + now.minute

    def to_min(h, m): return h * 60 + m

    for name, (sh, sm), (eh, em), color in SESSIONS:
        start = to_min(sh, sm)
        end   = to_min(eh, em)
        if name == "Asia":
            # wraps midnight
            active = mins >= start or mins < end
            if active:
                if mins >= start:
                    remaining = (24 * 60 - mins) + end
                else:
                    remaining = end - mins
                return {"session": name, "color": color, "active": True,
                        "remaining_min": remaining, "next": "London"}
        else:
            if start <= mins < end:
                remaining = end - mins
                idx = [s[0] for s in SESSIONS].index(name)
                next_s = SESSIONS[(idx + 1) % len(SESSIONS)][0]
                return {"session": name, "color": color, "active": True,
                        "remaining_min": remaining, "next": next_s}

    # Between sessions — find next
    next_name, next_color, mins_to_next = "London", "#00d4ff", 9999
    for name, (sh, sm), _, color in SESSIONS:
        start = to_min(sh, sm)
        if name == "Asia":
            if mins < 20 * 60:
                wait = to_min(sh, sm) + (24 * 60 - mins) if start < mins else start - mins
            else:
                wait = 24 * 60 - mins + to_min(sh, sm)
        else:
            wait = start - mins if start > mins else (24 * 60 - mins + start)
        if wait < mins_to_next:
            mins_to_next = wait
            next_name, next_color = name, color

    return {"session": "Closed", "color": "#44445a", "active": False,
            "remaining_min": mins_to_next, "next": next_name}


@st.cache_data(ttl=300)
def get_prices() -> list[dict]:
    """Fetch current price + daily change for each instrument via yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        return []

    result = []
    for ticker, name, code, color in INSTRUMENTS:
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            price = fi.last_price
            prev  = fi.previous_close
            if not price or not prev:
                hist = t.history(period="2d", interval="1d")
                if len(hist) >= 2:
                    price = float(hist["Close"].iloc[-1])
                    prev  = float(hist["Close"].iloc[-2])
                elif len(hist) == 1:
                    price = float(hist["Close"].iloc[0])
                    prev  = price
            change     = price - prev if price and prev else 0
            change_pct = change / prev * 100 if prev else 0
            result.append({
                "ticker": ticker, "name": name, "code": code, "color": color,
                "price": price or 0, "change": change, "change_pct": change_pct,
                "prev_close": prev or 0,
            })
        except Exception:
            result.append({
                "ticker": ticker, "name": name, "code": code, "color": color,
                "price": 0, "change": 0, "change_pct": 0, "prev_close": 0,
            })
    return result


@st.cache_data(ttl=900)
def get_news() -> list[dict]:
    """Fetch latest financial headlines from RSS feeds."""
    feeds = [
        ("Reuters Markets",   "https://feeds.reuters.com/reuters/businessNews"),
        ("ForexLive",         "https://www.forexlive.com/feed/news"),
        ("MarketWatch",       "https://feeds.marketwatch.com/marketwatch/topstories/"),
        ("Investing.com",     "https://www.investing.com/rss/news.rss"),
    ]
    headlines = []
    for source, url in feeds:
        try:
            resp = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                continue
            # Basic XML parse for title + link + pubDate
            from xml.etree import ElementTree as ET
            root = ET.fromstring(resp.content)
            ns = {"media": "http://search.yahoo.com/mrss/"}
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link")  or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()
                if title:
                    headlines.append({"source": source, "title": title,
                                      "link": link, "published": pub})
                if len(headlines) >= 20:
                    break
        except Exception:
            continue
    return headlines[:18]


def _fmt_eta(now: datetime, target: datetime) -> str:
    diff = int((target - now).total_seconds())
    if diff <= 0:
        return "now"
    h, r = divmod(diff, 3600)
    m = r // 60
    return f"{h}h {m}m" if h > 0 else f"{m}m"


def get_market_status() -> dict:
    """
    Return futures market open/closed status.
    CME Globex: open Sun 6pm ET → Fri 5pm ET, daily halt Mon-Thu 5-6pm ET.
    """
    now = datetime.now(EST)
    wd  = now.weekday()   # 0=Mon … 4=Fri, 5=Sat, 6=Sun
    tot = now.hour * 60 + now.minute

    CLOSE = 17 * 60   # 5:00 PM ET
    OPEN  = 18 * 60   # 6:00 PM ET

    # Saturday — always closed
    if wd == 5:
        sun_open = (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
        return {"open": False, "detail": f"Weekend — reopens Sun 6:00 PM ET · {_fmt_eta(now, sun_open)}"}

    # Sunday before 6 PM — closed
    if wd == 6 and tot < OPEN:
        opens = now.replace(hour=18, minute=0, second=0, microsecond=0)
        return {"open": False, "detail": f"Weekend — opens today 6:00 PM ET · {_fmt_eta(now, opens)}"}

    # Friday at or after 5 PM — weekend start
    if wd == 4 and tot >= CLOSE:
        sun_open = (now + timedelta(days=2)).replace(hour=18, minute=0, second=0, microsecond=0)
        return {"open": False, "detail": f"Weekend close — reopens Sun 6:00 PM ET · {_fmt_eta(now, sun_open)}"}

    # Mon–Thu daily maintenance 5–6 PM ET
    if wd < 4 and CLOSE <= tot < OPEN:
        opens = now.replace(hour=18, minute=0, second=0, microsecond=0)
        return {"open": False, "detail": f"Daily maintenance 5–6 PM ET — opens in {_fmt_eta(now, opens)}"}

    # Open — find next daily close
    next_close = now.replace(hour=17, minute=0, second=0, microsecond=0)
    if tot >= OPEN:
        # Past 6 PM — next close is tomorrow at 5 PM
        next_close += timedelta(days=1)
    return {"open": True, "detail": f"Closes {next_close.strftime('%a %H:%M ET')} · {_fmt_eta(now, next_close)}"}


@st.cache_data(ttl=3600)
def generate_tda(date_key: str, session_name: str, api_key: str) -> str:
    """Generate a CLS-methodology-based Top Down Analysis using Anthropic API.
    date_key is str(date.today()) — used as cache key, not a param passed to the model.
    Prices are fetched internally (already cached via get_prices).
    """
    if not api_key:
        return ""
    try:
        import anthropic
        from utils.methodology_loader import load_methodology

        methodology = load_methodology()
        prices = get_prices()   # already @st.cache_data(ttl=300)

        price_lines = "\n".join(
            f"  {p['code']}: ${p['price']:,.2f}  ({p['change_pct']:+.2f}%  vs prev close ${p['prev_close']:,.2f})"
            for p in prices if p.get("price")
        )

        today = datetime.now(EST)
        dow   = today.strftime("%A")

        prompt = f"""You are Jarvis, a CLS methodology trading analyst for Mala (a CLS/Mr.Casino student).

Today is {dow}, {today.strftime('%B %d, %Y')}. Current EST session: {session_name}.

Current market prices:
{price_lines}

Based on the CLS methodology and current prices, provide a concise Daily TDA in this exact format:

**HTF BIAS**
GC (Gold): [Bullish/Bearish/Neutral] — [1 sentence reason based on CLS rules]
ES (S&P): [Bullish/Bearish/Neutral] — [1 sentence reason]
NQ (Nasdaq): [Bullish/Bearish/Neutral] — [1 sentence reason]

**KEY LEVELS TO WATCH**
- [2-3 specific price levels or ranges with context — HTF liquidity, major zones, manipulation targets]

**SESSION EXPECTATION**
[2-3 sentences on what to expect for today's NY session based on manipulation cycle, liquidity, and {dow} tendencies]

**CLS SETUP WATCH**
[1-2 specific setup ideas aligned with methodology — include TF, direction, confirmation needed. Be specific, not generic.]

**RISK NOTE**
[1 sentence on the one thing to NOT do today based on current market context]

Keep the total response under 350 words. Be direct, methodology-driven, no fluff."""

        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model    = "claude-haiku-4-5-20251001",
            max_tokens = 600,
            system   = f"You are a CLS methodology analyst. Methodology context:\n\n{methodology[:6000]}",
            messages = [{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"[TDA generation error: {e}]"

from __future__ import annotations

import csv
import io
import json
import urllib.request
from datetime import datetime
from urllib.parse import quote
from urllib.error import URLError

POPULAR_VN_SYMBOLS = {"VNINDEX", "VNM", "FPT", "HPG", "VIC", "VCB", "SSI", "MWG", "VRE", "MBB", "ACB"}


def _fetch_json(url: str, timeout: float = 10, retries: int = 2) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(max(retries, 1)):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except (TimeoutError, URLError, OSError, ValueError, json.JSONDecodeError):
            continue
    return None

def fetch_stooq_daily_csv(symbol: str) -> list[tuple[str, float]]:
    """
    Stooq free CSV:
    https://stooq.com/q/d/l/?s=aapl.us&i=d
    Returns list of (YYYY-MM-DD, close).
    """
    url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&i=d"
    with urllib.request.urlopen(url, timeout=12) as resp:
        content = resp.read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    rows: list[tuple[str, float]] = []
    for r in reader:
        if not r.get("Date") or not r.get("Close"):
            continue
        try:
            _ = datetime.strptime(r["Date"], "%Y-%m-%d")
            rows.append((r["Date"], float(r["Close"])))
        except Exception:
            continue
    return rows


def moving_average_forecast(closes: list[float], window: int = 10) -> float | None:
    if len(closes) < max(3, window):
        return None
    tail = closes[-window:]
    return sum(tail) / len(tail)


def normalize_symbol_for_yahoo(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    if not s:
        return s
    if "." in s:
        return s
    if s in POPULAR_VN_SYMBOLS:
        return f"{s}.VN"
    return s


def fetch_yahoo_quote(symbol: str) -> dict | None:
    yahoo_symbol = normalize_symbol_for_yahoo(symbol)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={quote(yahoo_symbol)}"
    payload = _fetch_json(url, timeout=10, retries=3)
    if not payload:
        return None
    results = payload.get("quoteResponse", {}).get("result", [])
    if not results:
        return None
    r = results[0]
    return {
        "symbol": r.get("symbol") or yahoo_symbol,
        "name": r.get("shortName") or yahoo_symbol,
        "price": r.get("regularMarketPrice"),
        "change": r.get("regularMarketChange"),
        "change_percent": r.get("regularMarketChangePercent"),
        "open": r.get("regularMarketOpen"),
        "high": r.get("regularMarketDayHigh"),
        "low": r.get("regularMarketDayLow"),
        "volume": r.get("regularMarketVolume"),
        "previous_close": r.get("regularMarketPreviousClose"),
        "time": r.get("regularMarketTime"),
    }


def fetch_yahoo_intraday_closes(symbol: str, interval: str = "5m", range_: str = "1d") -> list[float]:
    yahoo_symbol = normalize_symbol_for_yahoo(symbol)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(yahoo_symbol)}"
        f"?interval={quote(interval)}&range={quote(range_)}"
    )
    payload = _fetch_json(url, timeout=10, retries=3)
    if not payload:
        return []
    result = payload.get("chart", {}).get("result") or []
    if not result:
        return []
    closes = result[0].get("indicators", {}).get("quote", [{}])[0].get("close") or []
    return [float(v) for v in closes if v is not None]


def fetch_yahoo_daily_rows(symbol: str, range_: str = "6mo") -> list[tuple[str, float]]:
    yahoo_symbol = normalize_symbol_for_yahoo(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(yahoo_symbol)}?interval=1d&range={quote(range_)}"
    payload = _fetch_json(url, timeout=10, retries=3)
    if not payload:
        return []
    result = payload.get("chart", {}).get("result") or []
    if not result:
        return []
    r0 = result[0]
    ts = r0.get("timestamp") or []
    closes = r0.get("indicators", {}).get("quote", [{}])[0].get("close") or []
    rows: list[tuple[str, float]] = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        rows.append((datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d"), float(c)))
    return rows


from __future__ import annotations

import json
import re
from datetime import date, datetime

from scrapling.fetchers import Fetcher

from intermarket_analysis.config import SeriesSpec, get_series
from intermarket_analysis.scrapers.utils import compute_fetch_range

SINA_KLINE = (
    "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
    "var=/InnerFuturesNewService.getDailyKLine?symbol={symbol}"
)


def fetch_sina_futures_kline(symbol: str, start: date, end: date) -> list[tuple[date, float]]:
    """Daily close for Chinese futures continuous (e.g. AU0, SC0) via Sina HTTP API."""
    url = SINA_KLINE.format(symbol=symbol.upper())
    resp = Fetcher.get(
        url,
        impersonate="chrome",
        timeout=45,
        headers={"Referer": "https://finance.sina.com.cn/"},
    )
    raw = resp.body if getattr(resp, "body", None) else (resp.text or "").encode("utf-8")
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
    match = re.search(r"\((\[.*\])\)\s*;?\s*$", text.strip(), re.S)
    if not match:
        match = re.search(r"\((\[.*\])\)", text, re.S)
    if not match:
        raise RuntimeError(f"Sina kline parse failed for {symbol}: {text[:200]!r}")

    rows = json.loads(match.group(1))
    out: list[tuple[date, float]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        day = row.get("d")
        close = row.get("c")
        if not day or close is None:
            continue
        try:
            obs = datetime.strptime(str(day), "%Y-%m-%d").date()
            val = float(str(close).replace(",", ""))
        except (TypeError, ValueError):
            continue
        if start <= obs <= end:
            out.append((obs, val))
    return sorted(out, key=lambda x: x[0])


def fetch_sina_series(spec: SeriesSpec, start: date, end: date) -> list[tuple[date, float]]:
    if not spec.sina_symbol:
        raise ValueError(f"{spec.series_id} missing sina_symbol")
    return fetch_sina_futures_kline(spec.sina_symbol, start, end)


def fetch_sina_series_incremental(
    series_id: str,
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    spec = get_series(series_id)
    if spec.scraper != "sina_futures":
        raise ValueError(f"{series_id} is not sina_futures")
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_sina_series(spec, start, end)

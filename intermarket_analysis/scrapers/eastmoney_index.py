from __future__ import annotations

import json
from datetime import date

from scrapling.fetchers import Fetcher

from intermarket_analysis.config import SeriesSpec, get_series
from intermarket_analysis.scrapers.utils import compute_fetch_range

KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.eastmoney.com/",
}

# secid format: market.indexcode (1=SH, 0=SZ)
EASTMONEY_SECID: dict[str, str] = {
    "sse_composite": "1.000001",
    "sse50": "1.000016",
    "csi300": "1.000300",
    "csi500": "1.000905",
    "csi1000": "1.000852",
    "szse_component": "0.399001",
    "chinext": "0.399006",
    "star50": "1.000688",
}


def _parse_klines(text: str, start: date, end: date) -> list[tuple[date, float]]:
    payload = json.loads(text)
    data = payload.get("data") if isinstance(payload, dict) else None
    lines = (data or {}).get("klines") if isinstance(data, dict) else None
    if not isinstance(lines, list):
        return []
    out: list[tuple[date, float]] = []
    for line in lines:
        if not isinstance(line, str) or "," not in line:
            continue
        parts = line.split(",")
        try:
            obs = date.fromisoformat(parts[0])
            close = float(parts[1])
        except (ValueError, IndexError):
            continue
        if start <= obs <= end:
            out.append((obs, close))
    return out


def fetch_eastmoney_index(spec: SeriesSpec, start: date, end: date) -> list[tuple[date, float]]:
    secid = EASTMONEY_SECID.get(spec.series_id)
    if not secid:
        raise ValueError(f"No Eastmoney secid for {spec.series_id}")
    resp = Fetcher.get(
        KLINE_URL,
        impersonate="chrome",
        timeout=90,
        headers=HEADERS,
        params={
            "fields1": "f1",
            "fields2": "f51,f52",
            "klt": "101",
            "fqt": "1",
            "secid": secid,
            "beg": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
        },
    )
    raw = resp.body if getattr(resp, "body", None) else b""
    if resp.status != 200 or not raw:
        raise RuntimeError(f"Eastmoney kline HTTP {resp.status} for {spec.series_id}")
    rows = _parse_klines(raw.decode("utf-8", errors="replace"), start, end)
    if not rows:
        raise RuntimeError(f"Eastmoney returned no rows for {spec.series_id}")
    dedup: dict[date, float] = {obs: val for obs, val in rows}
    return sorted(dedup.items(), key=lambda x: x[0])


def fetch_eastmoney_index_incremental(
    series_id: str,
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    spec = get_series(series_id)
    if spec.scraper != "eastmoney_index":
        raise ValueError(f"{series_id} is not an eastmoney_index series")
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_eastmoney_index(spec, start, end)

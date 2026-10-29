from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from urllib.parse import quote

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab
from intermarket_analysis.scrapers.investing_api import fetch_investing_history
from intermarket_analysis.scrapers.utils import (
    compute_fetch_range,
    parse_tv_history,
    try_http_history,
)


TV_SYMBOL_PAGE = "https://cn.tradingview.com/symbols/TVC-CN10Y/"
TV_CHART_PAGE = "https://cn.tradingview.com/chart/?symbol=TVC%3ACN10Y"
SYMBOL = "TVC:CN10Y"
HISTORY_HOSTS = (
    "https://tvc4.tradingview.com/history",
    "https://tvc3.tradingview.com/history",
    "https://history-data.tradingview.com/history",
)

# 10Y bond futures (price ~108–110 CNY); not the yield page (29227).
FUTURES_CHART_PAGE = "https://cn.investing.com/rates-bonds/10-year-t-bond-futures"
FUTURES_HISTORICAL_PAGE = (
    "https://cn.investing.com/rates-bonds/10-year-t-bond-futures-historical-data"
)
FUTURES_PAIR_ID = "1115125"

PRICE_MIN = 50.0
PRICE_MAX = 150.0


def _from_to_ts(start: date, end: date) -> tuple[int, int]:
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def _history_urls(start: date, end: date) -> list[str]:
    start_ts, end_ts = _from_to_ts(start, end)
    encoded = quote(SYMBOL, safe="")
    return [f"{host}?symbol={encoded}&resolution=1D&from={start_ts}&to={end_ts}" for host in HISTORY_HOSTS]


def _is_price_value(value: float) -> bool:
    return PRICE_MIN <= value <= PRICE_MAX


def _merge_tv_history(session, start: date, end: date, dedup: dict[date, float]) -> None:
    for response in session.network.search(url_pattern=r"history", limit=None):
        try:
            body = response.body
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            if not text or '"t":' not in text:
                continue
            payload = json.loads(text)
            for d, v in parse_tv_history(payload):
                if start <= d <= end and _is_price_value(v):
                    dedup[d] = v
        except Exception:
            continue


def _fetch_via_tradingview_browser(start: date, end: date) -> list[tuple[date, float]]:
    dedup: dict[date, float] = {}

    def _load(page_url: str) -> None:
        def _action(page) -> None:
            page.wait_for_timeout(4000)
            select_quote_mode_tab(page, "价格")
            page.wait_for_timeout(2000)
            select_chart_range(page, "5年", wait_ms=10000)

        with StealthySession(
            record_requests=True,
            max_recorded_requests=4000,
            **stealth_kwargs(),
        ) as session:
            session.fetch(page_url, network_idle=False, load_dom=True, page_action=_action)
            _merge_tv_history(session, start, end, dedup)

    for page_url in (TV_CHART_PAGE, TV_SYMBOL_PAGE):
        _load(page_url)
        if len(dedup) >= 50:
            break

    return sorted(dedup.items(), key=lambda x: x[0])


def _fetch_via_http(start: date, end: date) -> list[tuple[date, float]]:
    dedup: dict[date, float] = {}
    for url in _history_urls(start, end):
        base, _, query = url.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        payload = try_http_history(base, params=params, method="GET")
        if not payload:
            continue
        for d, v in parse_tv_history(payload):
            if start <= d <= end and _is_price_value(v):
                dedup[d] = v
    return sorted(dedup.items(), key=lambda x: x[0])


def _fetch_via_investing_futures_price(start: date, end: date) -> list[tuple[date, float]]:
    """China 10Y T-bond futures price (Investing CFTc1), ~same asset class as TV「价格」."""
    pair_id = FUTURES_PAIR_ID
    rows = fetch_investing_history(
        pair_id,
        start,
        end,
        chart_page=FUTURES_CHART_PAGE,
        range_label="5年",
        sbcharts_min_value=PRICE_MIN,
        sbcharts_abs_max=PRICE_MAX,
        pd_min_value=PRICE_MIN,
        pd_max_value=PRICE_MAX,
    )
    if len(rows) < 50:
        extra = fetch_investing_history(
            pair_id,
            start,
            end,
            chart_page=FUTURES_HISTORICAL_PAGE,
            range_label="5年",
            sbcharts_min_value=PRICE_MIN,
            sbcharts_abs_max=PRICE_MAX,
            pd_min_value=PRICE_MIN,
            pd_max_value=PRICE_MAX,
        )
        merged = {d: v for d, v in rows + extra if _is_price_value(v)}
        rows = sorted(merged.items(), key=lambda x: x[0])
    return [(d, v) for d, v in rows if _is_price_value(v)]


def _tv_http_enabled() -> bool:
    return os.environ.get("CN10Y_TRY_TRADINGVIEW", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def fetch_cn10y(start: date, end: date) -> list[tuple[date, float]]:
    """CN 10Y bond **price**; default source is Investing T-bond futures (no TradingView)."""
    dedup: dict[date, float] = {}
    loaders = [_fetch_via_investing_futures_price]
    if _tv_http_enabled():
        loaders.extend((_fetch_via_http, _fetch_via_tradingview_browser))

    for loader in loaders:
        for obs, value in loader(start, end):
            if start <= obs <= end and _is_price_value(value):
                dedup[obs] = value
        if len(dedup) >= 50:
            return sorted(dedup.items(), key=lambda x: x[0])
    return sorted(dedup.items(), key=lambda x: x[0])


def fetch_cn10y_incremental(
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_cn10y(start, end)

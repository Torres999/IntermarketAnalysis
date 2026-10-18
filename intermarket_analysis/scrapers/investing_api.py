from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range
from intermarket_analysis.scrapers.utils import parse_tv_history


def parse_investing_historical(payload: dict) -> list[tuple[date, float]]:
    rows = payload.get("data") or []
    if not isinstance(rows, list):
        return []
    out: list[tuple[date, float]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        obs = None
        if item.get("rowDateTimestamp"):
            obs = datetime.fromisoformat(str(item["rowDateTimestamp"]).replace("Z", "+00:00")).date()
        elif item.get("rowDateRaw"):
            obs = datetime.utcfromtimestamp(int(item["rowDateRaw"])).date()
        elif item.get("rowDate"):
            text = str(item["rowDate"]).strip()
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
                try:
                    obs = datetime.strptime(text, fmt).date()
                    break
                except ValueError:
                    continue
        close = item.get("last_closeRaw") or item.get("last_close") or item.get("close")
        if obs is None or close is None:
            continue
        try:
            out.append((obs, float(str(close).replace(",", ""))))
        except ValueError:
            continue
    return out


def parse_pd_instrument_candles(payload: dict) -> list[tuple[date, float]]:
    candles = payload.get("candles") or []
    out: list[tuple[date, float]] = []
    for item in candles:
        if not isinstance(item, dict):
            continue
        ts = item.get("t")
        close = item.get("c")
        if ts is None or close is None:
            continue
        try:
            obs = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date()
            out.append((obs, float(close)))
        except (TypeError, ValueError):
            continue
    return out


def parse_sbcharts_candles(payload: dict) -> list[tuple[date, float]]:
    candles = payload.get("candles") or []
    out: list[tuple[date, float]] = []
    for item in candles:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        ts_ms, value = item[0], item[1]
        if value is None:
            continue
        try:
            obs = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).date()
            out.append((obs, float(value)))
        except (TypeError, ValueError, OSError):
            continue
    return out


def historical_api_url(pair_id: str, start: date, end: date) -> str:
    return (
        f"https://api.investing.com/api/financialdata/historical/{pair_id}"
        f"?start-date={start.isoformat()}&end-date={end.isoformat()}"
        f"&time-frame=Daily&add-missing-rows=false"
    )


def resolve_pair_id(page_url: str, *, default: str) -> str:
    with StealthySession(record_requests=True, max_recorded_requests=500, **stealth_kwargs()) as session:
        session.fetch(page_url, network_idle=True)
        for resp in session.network.search(url_pattern=r"financialdata/historical/", limit=None):
            match = re.search(r"historical/(\d+)", resp.url)
            if match and match.group(1) != "0":
                return match.group(1)
        for resp in session.network.search(url_pattern=r"tvc4\.investing\.com/.+/history\?", limit=None):
            match = re.search(r"symbol=(\d+)", resp.url)
            if match and match.group(1) != "0":
                return match.group(1)
    return default


def _merge_points(dedup: dict[date, float], rows: list[tuple[date, float]], start: date, end: date) -> None:
    for obs, value in rows:
        if start <= obs <= end:
            dedup[obs] = value


def _collect_historical_table_api(
    session,
    pair_id: str,
    start: date,
    end: date,
    dedup: dict[date, float],
) -> None:
    for response in session.network.search(
        url_pattern=rf"financialdata/historical/{pair_id}",
        limit=None,
    ):
        try:
            body = response.body
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                continue
            _merge_points(dedup, parse_investing_historical(payload), start, end)
        except Exception:
            continue


def _looks_like_yield_series(rows: list[tuple[date, float]], *, max_value: float) -> bool:
    if not rows:
        return False
    sample = [value for _, value in rows[:5] + rows[-5:]]
    return max(sample) <= max_value


def _looks_like_price_series(rows: list[tuple[date, float]], *, min_value: float) -> bool:
    if not rows:
        return False
    sample = [value for _, value in rows[:5] + rows[-5:]]
    return min(sample) >= min_value


def _collect_pd_instrument_candles(
    session,
    instrument_id: str,
    start: date,
    end: date,
    dedup: dict[date, float],
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> None:
    interval_rank = {"p1d": 3, "p1w": 2, "p1m": 1, "pt15m": 0}
    responses: list[tuple[int, str, bytes | str | None]] = []
    pattern = rf"pd-instruments/v1/instruments/{instrument_id}/charts/candles/"
    for response in session.network.search(url_pattern=pattern, limit=None):
        interval = "other"
        for key in interval_rank:
            if f"/candles/{key}" in response.url:
                interval = key
                break
        responses.append((interval_rank.get(interval, -1), response.url, response.body))
    responses.sort(key=lambda item: item[0], reverse=True)
    for _rank, _url, body in responses:
        try:
            if not body:
                continue
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            payload = json.loads(text)
            if isinstance(payload, dict):
                rows = parse_pd_instrument_candles(payload)
                if min_value is not None and not _looks_like_price_series(rows, min_value=min_value):
                    continue
                if max_value is not None and not _looks_like_yield_series(rows, max_value=max_value):
                    continue
                _merge_points(dedup, rows, start, end)
        except Exception:
            continue


def _collect_chart_timeframe_data(
    session,
    start: date,
    end: date,
    dedup: dict[date, float],
    *,
    range_label: str,
    sbcharts_max_value: float | None = None,
    sbcharts_min_value: float | None = None,
    sbcharts_abs_max: float | None = None,
) -> None:
    """Chart footer timeframe (e.g. 5年) loads sbcharts JSON and TV history on Investing."""
    sb_responses: list[tuple[int, str, bytes | str | None]] = []
    for response in session.network.search(url_pattern=r"sbcharts\.investing\.com/.*\.json", limit=None):
        url = response.url
        priority = 0
        if "_5years.json" in url or "_5year.json" in url:
            priority = 3
        elif "_max.json" in url:
            priority = 2
        elif "_1year.json" in url or "_1years.json" in url:
            priority = 1
        else:
            priority = 0
        sb_responses.append((priority, url, response.body))

    sb_responses.sort(key=lambda item: item[0], reverse=True)
    if range_label == "5年":
        preferred = [item for item in sb_responses if item[0] >= 2]
        if preferred:
            sb_responses = preferred

    seen_urls: set[str] = set()
    for _priority, url, body in sb_responses:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            if not body:
                continue
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            payload = json.loads(text)
            if isinstance(payload, dict):
                rows = parse_sbcharts_candles(payload)
                if sbcharts_max_value is not None and not _looks_like_yield_series(rows, max_value=sbcharts_max_value):
                    continue
                if sbcharts_min_value is not None and not _looks_like_price_series(rows, min_value=sbcharts_min_value):
                    continue
                if sbcharts_abs_max is not None and rows and max(v for _, v in rows) > sbcharts_abs_max:
                    continue
                _merge_points(dedup, rows, start, end)
        except Exception:
            continue

    for response in session.network.search(url_pattern=r"tvc4\.investing\.com/.+/history\?", limit=None):
        try:
            body = response.body
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            if not text:
                continue
            payload = json.loads(text)
            if isinstance(payload, dict):
                _merge_points(dedup, parse_tv_history(payload), start, end)
        except Exception:
            continue


def fetch_investing_history(
    pair_id: str,
    start: date,
    end: date,
    *,
    chart_page: str,
    range_label: str = "5年",
    sbcharts_max_value: float | None = None,
    sbcharts_min_value: float | None = None,
    pd_min_value: float | None = None,
    pd_max_value: float | None = None,
    sbcharts_abs_max: float | None = None,
    quote_tab: str | None = None,
) -> list[tuple[date, float]]:
    """Open Investing chart page, click timeframe (5年), read chart APIs from network."""
    dedup: dict[date, float] = {}

    def _dismiss_overlays(page) -> None:
        try:
            page.evaluate(
                """() => {
                    const wall = document.querySelector('#regwall-container');
                    if (wall) wall.remove();
                }"""
            )
        except Exception:
            pass

    def _action(page) -> None:
        page.wait_for_timeout(2500)
        _dismiss_overlays(page)
        if quote_tab:
            from intermarket_analysis.scrapers.browser_ui import select_quote_mode_tab

            select_quote_mode_tab(page, quote_tab)
        select_chart_range(page, range_label)

    with StealthySession(record_requests=True, max_recorded_requests=2000, **stealth_kwargs()) as session:
        session.fetch(chart_page, network_idle=True, page_action=_action)
        _collect_chart_timeframe_data(
            session,
            start,
            end,
            dedup,
            range_label=range_label,
            sbcharts_max_value=sbcharts_max_value,
            sbcharts_min_value=sbcharts_min_value,
            sbcharts_abs_max=sbcharts_abs_max,
        )
        _collect_pd_instrument_candles(
            session,
            pair_id,
            start,
            end,
            dedup,
            min_value=pd_min_value,
            max_value=pd_max_value,
        )
        _collect_historical_table_api(session, pair_id, start, end, dedup)

    if len(dedup) < 80 and range_label == "5年":
        def _action_max(page) -> None:
            page.wait_for_timeout(2500)
            _dismiss_overlays(page)
            if quote_tab:
                from intermarket_analysis.scrapers.browser_ui import select_quote_mode_tab

                select_quote_mode_tab(page, quote_tab)
            select_chart_range(page, "最大值")

        with StealthySession(record_requests=True, max_recorded_requests=2000, **stealth_kwargs()) as session:
            session.fetch(chart_page, network_idle=True, page_action=_action_max)
            _collect_chart_timeframe_data(
                session,
                start,
                end,
                dedup,
                range_label="最大值",
                sbcharts_max_value=sbcharts_max_value,
                sbcharts_min_value=sbcharts_min_value,
                sbcharts_abs_max=sbcharts_abs_max,
            )
            _collect_pd_instrument_candles(
                session,
                pair_id,
                start,
                end,
                dedup,
                min_value=pd_min_value,
                max_value=pd_max_value,
            )
            _collect_historical_table_api(session, pair_id, start, end, dedup)

    if pd_max_value is not None or sbcharts_abs_max is not None:
        cap = sbcharts_abs_max or pd_max_value
        if cap is not None:
            dedup = {d: v for d, v in dedup.items() if v <= cap}

    return sorted(dedup.items(), key=lambda x: x[0])

from __future__ import annotations

import json
import time
from calendar import monthrange
from datetime import date

from scrapling.fetchers import Fetcher

from intermarket_analysis.scrapers.utils import compute_fetch_range

CHINAMONEY_YIELD_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ClsYldCurvHis"
REFERER = "https://www.chinamoney.com.cn/chinese/bkcurvclosedyhis/"
BOND_TYPE_GOV = "CYCC000"
TENOR_YEARS = 10.0


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def _month_chunks(start: date, end: date) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        ms, me = _month_bounds(y, m)
        chunk_start = max(start, ms)
        chunk_end = min(end, me)
        if chunk_start <= chunk_end:
            chunks.append((chunk_start, chunk_end))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return chunks


def _parse_yield_records(payload: dict) -> list[tuple[date, float]]:
    records = payload.get("records") or []
    out: list[tuple[date, float]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        try:
            tenor = float(str(item.get("yearTermStr", "")).strip())
        except ValueError:
            continue
        if abs(tenor - TENOR_YEARS) > 0.05:
            continue
        raw_date = item.get("newDateValueCN") or item.get("newDateValue") or ""
        text = str(raw_date).strip()
        obs: date | None = None
        if len(text) >= 10 and text[4] == "-":
            obs = date.fromisoformat(text[:10])
        elif len(text) >= 11 and " " in text:
            # e.g. "28 Oct 2026"
            from datetime import datetime

            obs = datetime.strptime(text, "%d %b %Y").date()
        ytext = str(item.get("maturityYieldStr") or "").strip()
        if obs is None or not ytext or ytext == "---":
            continue
        try:
            out.append((obs, float(ytext)))
        except ValueError:
            continue
    return out


def _fetch_month(start: date, end: date) -> list[tuple[date, float]]:
    dedup: dict[date, float] = {}
    page_num = 1
    while page_num <= 30:
        resp = Fetcher.get(
            CHINAMONEY_YIELD_URL,
            impersonate="chrome",
            timeout=60,
            headers={"Referer": REFERER, "Origin": "https://www.chinamoney.com.cn"},
            params={
                "lang": "CN",
                "reference": "1,2,3",
                "bondType": BOND_TYPE_GOV,
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "termId": "1",
                "pageNum": str(page_num),
                "pageSize": "50",
            },
        )
        raw = resp.body if getattr(resp, "body", None) else b""
        if resp.status != 200 or not raw:
            if page_num == 1:
                raise RuntimeError(
                    f"chinamoney yield HTTP {resp.status} ({start}..{end})"
                )
            break
        payload = json.loads(raw.decode("utf-8", errors="replace"))
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid chinamoney yield JSON")
        batch = _parse_yield_records(payload)
        if not batch:
            break
        for obs, value in batch:
            if start <= obs <= end:
                dedup[obs] = value
        if len(payload.get("records") or []) < 50:
            break
        page_num += 1
        time.sleep(0.15)
    return sorted(dedup.items(), key=lambda x: x[0])


def _fetch_investing_recent(start: date, end: date) -> list[tuple[date, float]]:
    from intermarket_analysis.scrapers.investing_api import fetch_investing_history

    page = "https://cn.investing.com/rates-bonds/china-10-year-bond-yield-historical-data"
    return fetch_investing_history(
        "29227",
        start,
        end,
        chart_page=page,
        sbcharts_max_value=15.0,
        pd_max_value=15.0,
    )


def fetch_cn10y_yield(start: date, end: date) -> list[tuple[date, float]]:
    dedup: dict[date, float] = {}
    for chunk_start, chunk_end in _month_chunks(start, end):
        for obs, value in _fetch_month(chunk_start, chunk_end):
            dedup[obs] = value
        time.sleep(0.1)
    for obs, value in _fetch_investing_recent(start, end):
        if start <= obs <= end:
            dedup[obs] = value
    return sorted(dedup.items(), key=lambda x: x[0])


def fetch_cn10y_yield_incremental(
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_cn10y_yield(start, end)

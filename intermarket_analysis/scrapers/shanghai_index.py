from __future__ import annotations

from datetime import date

from intermarket_analysis.scrapers.eastmoney_index import fetch_eastmoney_index_incremental


def fetch_sse_composite(start: date, end: date) -> list[tuple[date, float]]:
    from intermarket_analysis.config import get_series
    from intermarket_analysis.scrapers.eastmoney_index import fetch_eastmoney_index

    return fetch_eastmoney_index(get_series("sse_composite"), start, end)


def fetch_sse_composite_incremental(
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    return fetch_eastmoney_index_incremental("sse_composite", last_obs, end)

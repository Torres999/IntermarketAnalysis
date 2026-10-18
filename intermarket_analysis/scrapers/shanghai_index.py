from __future__ import annotations

from datetime import date

from intermarket_analysis.scrapers.investing_api import fetch_investing_history, resolve_pair_id
from intermarket_analysis.scrapers.utils import compute_fetch_range


CHART_PAGE = "https://cn.investing.com/indices/shanghai-composite-chart"
DEFAULT_PAIR_ID = "40820"


def fetch_sse_composite(start: date, end: date) -> list[tuple[date, float]]:
    pair_id = resolve_pair_id(CHART_PAGE, default=DEFAULT_PAIR_ID)
    return fetch_investing_history(
        pair_id,
        start,
        end,
        chart_page=CHART_PAGE,
        range_label="5年",
    )


def fetch_sse_composite_incremental(
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_sse_composite(start, end)

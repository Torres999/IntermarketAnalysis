from __future__ import annotations

from datetime import date

from intermarket_analysis.config import SeriesSpec, get_series
from intermarket_analysis.scrapers.investing_api import (
    chart_page_candidates,
    fetch_investing_history,
)
from intermarket_analysis.scrapers.utils import compute_fetch_range


def fetch_investing_series(spec: SeriesSpec, start: date, end: date) -> list[tuple[date, float]]:
    pair_id = spec.default_pair_id or "0"
    best: list[tuple[date, float]] = []
    last_error: Exception | None = None
    for chart_page in chart_page_candidates(spec.source_url):
        try:
            rows = fetch_investing_history(
                pair_id,
                start,
                end,
                chart_page=chart_page,
                range_label=spec.range_label,
                sbcharts_max_value=spec.sbcharts_max_value,
                sbcharts_min_value=spec.sbcharts_min_value,
                pd_max_value=spec.pd_max_value,
                pd_min_value=spec.pd_min_value,
                quote_tab=spec.quote_tab,
            )
            if len(rows) > len(best):
                best = rows
            if len(rows) >= 80:
                return rows
        except Exception as exc:
            last_error = exc
            continue
    if best:
        return best
    if last_error:
        raise last_error
    return []


def fetch_investing_series_incremental(
    series_id: str,
    last_obs: date | None,
    end: date | None = None,
) -> list[tuple[date, float]]:
    spec = get_series(series_id)
    if spec.scraper != "investing_chart":
        raise ValueError(f"{series_id} is not an investing_chart series")
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_investing_series(spec, start, end)

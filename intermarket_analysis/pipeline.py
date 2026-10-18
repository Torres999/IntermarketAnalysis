from __future__ import annotations

import traceback
from datetime import date

from intermarket_analysis.scrapers.cn10y import fetch_cn10y_incremental
from intermarket_analysis.scrapers.rmb_index import fetch_rmb_indices_incremental
from intermarket_analysis.scrapers.shanghai_index import fetch_sse_composite_incremental
from intermarket_analysis.storage import (
    clear_series_data,
    get_last_obs_date,
    init_db,
    record_error,
    upsert_observations,
)


def run_incremental_scrape(end: date | None = None) -> dict[str, int | str]:
    """Scrape all configured series and persist to SQLite."""
    end = end or date.today()
    init_db()
    summary: dict[str, int | str] = {"end_date": end.isoformat()}

    try:
        points = fetch_cn10y_incremental(get_last_obs_date("cn10y"), end)
        summary["cn10y"] = upsert_observations("cn10y", points)
    except Exception as exc:
        record_error("cn10y", str(exc))
        summary["cn10y_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"

    try:
        last = get_last_obs_date("rmb_cfets") or get_last_obs_date("rmb_bis")
        bundles = fetch_rmb_indices_incremental(last, end)
        for series_id, rows in bundles.items():
            summary[series_id] = upsert_observations(series_id, rows)
    except Exception as exc:
        for sid in ("rmb_cfets", "rmb_bis", "rmb_sdr"):
            record_error(sid, str(exc))
        summary["rmb_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"

    try:
        points = fetch_sse_composite_incremental(get_last_obs_date("sse_composite"), end)
        summary["sse_composite"] = upsert_observations("sse_composite", points)
    except Exception as exc:
        record_error("sse_composite", str(exc))
        summary["sse_composite_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"

    return summary


def run_backfill_chart_series(end: date | None = None) -> dict[str, int | str]:
    """Clear and re-fetch 5Y chart-based series (SSE, CN10Y)."""
    end = end or date.today()
    init_db()
    clear_series_data(["cn10y", "sse_composite"])
    return run_incremental_scrape(end)

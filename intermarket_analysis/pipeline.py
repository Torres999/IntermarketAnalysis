from __future__ import annotations

import traceback
from datetime import date

from intermarket_analysis.config import (
    chart_backfill_series_ids,
    default_start,
    eastmoney_index_series,
    enabled_series,
    investing_chart_series,
    sina_futures_series,
)
from intermarket_analysis.scrapers.cn10y import fetch_cn10y_incremental
from intermarket_analysis.scrapers.cn10y_yield import fetch_cn10y_yield_incremental
from intermarket_analysis.scrapers.commodity_composite import refresh_nh_commodity_proxy
from intermarket_analysis.scrapers.eastmoney_index import fetch_eastmoney_index_incremental
from intermarket_analysis.scrapers.investing_series import fetch_investing_series_incremental
from intermarket_analysis.scrapers.rmb_index import fetch_rmb_indices_incremental
from intermarket_analysis.scrapers.sina_futures import fetch_sina_series_incremental
from intermarket_analysis.storage import (
    clear_series_data,
    get_last_obs_date,
    init_db,
    record_error,
    upsert_observations,
)


def _log(msg: str) -> None:
    print(msg, flush=True)


def _scrape_eastmoney_indices(end: date, summary: dict[str, int | str]) -> None:
    specs = eastmoney_index_series()
    for i, spec in enumerate(specs, 1):
        sid = spec.series_id
        _log(f"[{i}/{len(specs)}] Eastmoney index: {sid} …")
        try:
            points = fetch_eastmoney_index_incremental(sid, get_last_obs_date(sid), end)
            summary[sid] = upsert_observations(sid, points)
            _log(f"  -> {summary[sid]} rows upserted")
        except Exception as exc:
            record_error(sid, str(exc))
            summary[f"{sid}_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"
            _log(f"  -> ERROR: {exc}")


def _scrape_investing_charts(end: date, summary: dict[str, int | str]) -> None:
    specs = investing_chart_series()
    for i, spec in enumerate(specs, 1):
        sid = spec.series_id
        _log(f"[{i}/{len(specs)}] Investing chart: {sid} …")
        try:
            points = fetch_investing_series_incremental(
                sid, get_last_obs_date(sid), end
            )
            summary[sid] = upsert_observations(sid, points)
            _log(f"  -> {summary[sid]} rows upserted")
        except Exception as exc:
            record_error(sid, str(exc))
            summary[f"{sid}_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"
            _log(f"  -> ERROR: {exc}")


def _scrape_sina_commodities(end: date, summary: dict[str, int | str]) -> None:
    specs = sina_futures_series()
    for spec in specs:
        sid = spec.series_id
        _log(f"Sina futures: {sid} …")
        try:
            points = fetch_sina_series_incremental(sid, get_last_obs_date(sid), end)
            summary[sid] = upsert_observations(sid, points)
            _log(f"  -> {summary[sid]} rows")
        except Exception as exc:
            record_error(sid, str(exc))
            summary[f"{sid}_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"
            _log(f"  -> ERROR: {exc}")


def _refresh_composite(end: date, summary: dict[str, int | str]) -> None:
    start = default_start(end)
    _log("Building nh_commodity composite …")
    try:
        summary["nh_commodity"] = refresh_nh_commodity_proxy(start, end)
        _log(f"  -> {summary['nh_commodity']} rows")
    except Exception as exc:
        record_error("nh_commodity", str(exc))
        summary["nh_commodity_error"] = str(exc)


def run_incremental_scrape(end: date | None = None) -> dict[str, int | str]:
    """Scrape all configured series and persist to SQLite."""
    end = end or date.today()
    init_db()
    summary: dict[str, int | str] = {
        "end_date": end.isoformat(),
        "series_enabled": len(enabled_series()),
    }

    _log("CN10Y bond price (Investing 10Y futures chart) …")
    try:
        points = fetch_cn10y_incremental(get_last_obs_date("cn10y"), end)
        summary["cn10y"] = upsert_observations("cn10y", points)
        _log(f"  -> cn10y {summary['cn10y']} rows")
    except Exception as exc:
        record_error("cn10y", str(exc))
        summary["cn10y_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"
        _log(f"  -> cn10y ERROR: {exc}")

    _log("CN10Y bond yield (chinamoney curve API) …")
    try:
        points = fetch_cn10y_yield_incremental(get_last_obs_date("cn10y_yield"), end)
        summary["cn10y_yield"] = upsert_observations("cn10y_yield", points)
        _log(f"  -> cn10y_yield {summary['cn10y_yield']} rows")
    except Exception as exc:
        record_error("cn10y_yield", str(exc))
        summary["cn10y_yield_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"
        _log(f"  -> cn10y_yield ERROR: {exc}")

    _scrape_eastmoney_indices(end, summary)

    _scrape_investing_charts(end, summary)

    _log("RMB indices (chinamoney HTTP) …")
    try:
        last = get_last_obs_date("rmb_cfets") or get_last_obs_date("rmb_bis")
        bundles = fetch_rmb_indices_incremental(last, end)
        for series_id, rows in bundles.items():
            summary[series_id] = upsert_observations(series_id, rows)
            _log(f"  -> {series_id} {summary[series_id]} rows")
    except Exception as exc:
        for sid in ("rmb_cfets", "rmb_bis", "rmb_sdr"):
            record_error(sid, str(exc))
        summary["rmb_error"] = f"{exc}\n{traceback.format_exc(limit=2)}"
        _log(f"  -> rmb ERROR: {exc}")

    _scrape_sina_commodities(end, summary)
    _refresh_composite(end, summary)
    _log("Scrape pass finished.")
    return summary


def run_backfill_chart_series(end: date | None = None) -> dict[str, int | str]:
    """Clear and re-fetch chart-based series (Investing 5Y + CN10Y)."""
    end = end or date.today()
    init_db()
    clear_series_data(chart_backfill_series_ids())
    return run_incremental_scrape(end)


def bootstrap_if_empty(end: date | None = None) -> dict[str, int | str]:
    """If core series have almost no rows, run a chart backfill once."""
    end = end or date.today()
    init_db()
    from intermarket_analysis.storage import connect

    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM observations").fetchone()
        total = int(row["c"]) if row else 0
    if total > 500:
        return {"bootstrap": "skipped", "observations": total}
    _log("First run: backfilling chart-based series (this can take 10–20 min) …")
    clear_series_data(chart_backfill_series_ids())
    summary = run_incremental_scrape(end)
    summary["bootstrap"] = "backfill_charts"
    return summary

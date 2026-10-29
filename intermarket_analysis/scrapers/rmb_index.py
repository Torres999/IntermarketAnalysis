from __future__ import annotations

import time
from datetime import date, datetime

from intermarket_analysis.scrapers.utils import browser_fetch_excel_post, compute_fetch_range, http_fetch_excel_post
from intermarket_analysis.xlsx_minimal import read_first_sheet_rows


def _normalize_date(raw: str) -> date | None:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    if len(raw) >= 10 and raw[4] == "-":
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    return None


def _year_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Chinamoney Excel export returns empty sheets for very long ranges."""
    chunks: list[tuple[date, date]] = []
    year = start.year
    while year <= end.year:
        chunk_start = max(start, date(year, 1, 1))
        chunk_end = min(end, date(year, 12, 31))
        if chunk_start <= chunk_end:
            chunks.append((chunk_start, chunk_end))
        year += 1
    return chunks


def _parse_excel_rows(
    rows: list[list[str]],
    start: date,
    end: date,
) -> dict[str, list[tuple[date, float]]]:
    if len(rows) < 2:
        return {"rmb_cfets": [], "rmb_bis": [], "rmb_sdr": []}

    header = [c.strip() for c in rows[0]]
    cfets_idx, bis_idx, sdr_idx = 1, 2, 3
    for i, name in enumerate(header):
        upper = name.upper()
        if "CFETS" in upper:
            cfets_idx = i
        elif "BIS" in upper:
            bis_idx = i
        elif "SDR" in upper:
            sdr_idx = i

    out: dict[str, list[tuple[date, float]]] = {
        "rmb_cfets": [],
        "rmb_bis": [],
        "rmb_sdr": [],
    }
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        first = str(row[0]).strip()
        if "来源" in first or "chinamoney" in first.lower():
            continue
        obs = _normalize_date(first)
        if obs is None or obs < start or obs > end:
            continue

        def _val(idx: int) -> float | None:
            if idx >= len(row):
                return None
            try:
                return float(str(row[idx]).replace(",", ""))
            except ValueError:
                return None

        for key, idx in (
            ("rmb_cfets", cfets_idx),
            ("rmb_bis", bis_idx),
            ("rmb_sdr", sdr_idx),
        ):
            v = _val(idx)
            if v is not None:
                out[key].append((obs, v))
    return out


def fetch_rmb_indices(
    start: date,
    end: date,
) -> dict[str, list[tuple[date, float]]]:
    """Return CFETS/BIS/SDR RMB index series from chinamoney Excel export."""
    page_url = "https://www.chinamoney.com.cn/chinese/bkrmbidx/"
    merged: dict[str, dict[date, float]] = {
        "rmb_cfets": {},
        "rmb_bis": {},
        "rmb_sdr": {},
    }

    for chunk_start, chunk_end in _year_chunks(start, end):
        t_ms = int(time.time() * 1000)
        excel_url = (
            "https://www.chinamoney.com.cn/dqs/rest/cm-u-bk-fx/RmbIdxHisExcel"
            f"?lang=CN&startDate={chunk_start.isoformat()}&endDate={chunk_end.isoformat()}&t={t_ms}"
        )
        try:
            content = http_fetch_excel_post(page_url, excel_url)
        except RuntimeError:
            content = browser_fetch_excel_post(page_url, excel_url, headless=True)
        rows = read_first_sheet_rows(content)
        part = _parse_excel_rows(rows, chunk_start, chunk_end)
        for key, points in part.items():
            for obs, val in points:
                merged[key][obs] = val

    return {
        key: sorted(series.items(), key=lambda x: x[0])
        for key, series in merged.items()
    }


def fetch_rmb_indices_incremental(
    last_obs: date | None,
    end: date | None = None,
) -> dict[str, list[tuple[date, float]]]:
    end = end or date.today()
    start, end = compute_fetch_range(last_obs, end)
    return fetch_rmb_indices(start, end)

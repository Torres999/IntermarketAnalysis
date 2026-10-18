from __future__ import annotations

import base64
import json
import re
from datetime import date, timedelta
from typing import Any, Callable

from scrapling.fetchers import Fetcher, StealthyFetcher, StealthySession

from intermarket_analysis.browser_config import stealth_kwargs


def compute_fetch_range(
    last_obs: date | None,
    end: date,
    *,
    initial_years: int = 5,
    overlap_days: int = 7,
) -> tuple[date, date]:
    if last_obs is None:
        start = end - timedelta(days=365 * initial_years)
    else:
        start = last_obs - timedelta(days=overlap_days)
    if start > end:
        start = end
    return start, end


def browser_fetch_excel_post(
    page_url: str,
    excel_url: str,
    *,
    headless: bool = True,
) -> bytes:
    payload: dict[str, Any] = {}

    def _action(page) -> None:
        result = page.evaluate(
            """async (url) => {
                const resp = await fetch(url, { method: 'POST', credentials: 'include' });
                const buf = await resp.arrayBuffer();
                let binary = '';
                const bytes = new Uint8Array(buf);
                const chunk = 0x8000;
                for (let i = 0; i < bytes.length; i += chunk) {
                    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                }
                return { status: resp.status, b64: btoa(binary) };
            }""",
            excel_url,
        )
        payload.update(result)

    StealthyFetcher.fetch(
        page_url,
        network_idle=True,
        page_action=_action,
        **stealth_kwargs(headless=headless),
    )
    if payload.get("status") != 200:
        raise RuntimeError(f"Excel download failed HTTP {payload.get('status')}")
    return base64.b64decode(payload["b64"])


def capture_network_json(
    page_url: str,
    *,
    url_pattern: str,
    wait_after_load: Callable | None = None,
    headless: bool = True,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    with StealthySession(
        record_requests=True,
        max_recorded_requests=2000,
        **stealth_kwargs(headless=headless),
    ) as session:
        def _action(page) -> None:
            if wait_after_load:
                wait_after_load(page)

        session.fetch(
            page_url,
            network_idle=True,
            page_action=_action if wait_after_load else None,
        )
        for response in session.network.search(url_pattern=url_pattern, limit=None):
            try:
                body = response.body
                if not body:
                    continue
                if isinstance(body, bytes):
                    text = body.decode("utf-8", errors="replace")
                else:
                    text = str(body)
                collected.append(json.loads(text))
            except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
                continue
    return collected


def try_http_history(
    url: str,
    *,
    params: dict[str, str | int] | None = None,
    method: str = "GET",
) -> dict[str, Any] | None:
    try:
        if method.upper() == "POST":
            resp = Fetcher.post(url, impersonate="chrome", json=params or {})
        else:
            resp = Fetcher.get(url, impersonate="chrome", params=params or {})
        if resp.status != 200 or not resp.text:
            return None
        return json.loads(resp.text)
    except Exception:
        return None


def parse_tv_history(payload: dict[str, Any]) -> list[tuple[date, float]]:
    if payload.get("s") != "ok":
        return []
    times = payload.get("t") or []
    closes = payload.get("c") or []
    out: list[tuple[date, float]] = []
    for ts, close in zip(times, closes):
        if close is None:
            continue
        out.append((date.fromtimestamp(int(ts)), float(close)))
    return out


def find_first_regex(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def year_chunks(start: date, end: date) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    year = start.year
    while year <= end.year:
        chunk_start = max(start, date(year, 1, 1))
        chunk_end = min(end, date(year, 12, 31))
        if chunk_start <= chunk_end:
            chunks.append((chunk_start, chunk_end))
        year += 1
    return chunks


def playwright_get_json(page, url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any] | None:
    """HTTP GET via Playwright browser context (same route as the page; no page CORS)."""
    try:
        response = page.context.request.get(url, headers=headers or {})
        if not response.ok:
            return None
        return response.json()
    except Exception:
        return None

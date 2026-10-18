import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def action(page) -> None:
    page.wait_for_timeout(3000)
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(2000)
    select_chart_range(page, "5年", wait_ms=12000)


with StealthySession(record_requests=True, max_recorded_requests=5000, **stealth_kwargs()) as session:
    page = session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"history", limit=None):
        text = resp.body.decode("utf-8", errors="replace") if isinstance(resp.body, bytes) else str(resp.body)
        if len(text) < 50:
            continue
        print("HIST", resp.url[:120], "len", len(text))
        try:
            pts = parse_tv_history(json.loads(text))
            print("  pts", len(pts), pts[:2], pts[-2:] if pts else None)
        except Exception as exc:
            print("  parse err", exc, text[:100])

    for resp in session.network.search(limit=None):
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body or "")
        if "100.6" in text or '"t":[' in text:
            print("BODYHIT", resp.url[:120], "len", len(text))
            if '"t":' in text and '"c":' in text:
                print(text[:300])
        url = resp.url
        if "tradingview.com" not in url:
            continue
        if any(k in url for k in ("history", "quotes", "symbol", "timescale", "candles", "widget")):
            blen = len(body or b"")
            if blen > 200:
                print(blen, url[:140])

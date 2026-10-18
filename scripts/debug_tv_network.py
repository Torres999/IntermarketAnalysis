import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/?timeframe=12M"


def action(page) -> None:
    page.wait_for_timeout(10000)
    page.mouse.wheel(0, 2000)
    page.wait_for_timeout(3000)


with StealthySession(record_requests=True, max_recorded_requests=5000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(limit=None):
        body = resp.body
        if not body:
            continue
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if '"t":[' in text and '"c":[' in text:
            print("HISTORY?", resp.url[:160])
            print(text[:200])
        if "CN10Y" in text and len(text) < 5000:
            print("CN10Y snippet", resp.url[:120], text[:400])

import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range

URLS = [
    "https://cn.investing.com/indices/shanghai-composite",
    "https://cn.investing.com/indices/shanghai-composite-chart",
]


def action(page) -> None:
    page.wait_for_timeout(3000)
    select_chart_range(page, "5年", wait_ms=8000)


for url in URLS:
    print("\n===", url)
    with StealthySession(record_requests=True, max_recorded_requests=3000, **stealth_kwargs()) as session:
        page = session.fetch(url, network_idle=True, page_action=action)
        html = page.html_content or ""
        nd = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
        if nd:
            data = json.loads(nd.group(1))
            pp = data.get("props", {}).get("pageProps", {})
            print("__NEXT_DATA__ keys:", list(pp.keys())[:20])
            state = pp.get("state") or {}
            print("state keys:", list(state.keys())[:30])
        hits = []
        for resp in session.network.search(limit=None):
            u = resp.url
            if any(
                k in u.lower()
                for k in (
                    "financial",
                    "historical",
                    "chart",
                    "api.investing",
                    "symbol",
                    "timeseries",
                )
            ):
                body = resp.body
                blen = len(body) if body else 0
                hits.append((blen, u[:160]))
        hits.sort(reverse=True)
        print("network hits", len(hits))
        for blen, u in hits[:25]:
            print(" ", blen, u)

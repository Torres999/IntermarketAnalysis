from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/?timeframe=12M"

with StealthySession(record_requests=True, max_recorded_requests=5000, **stealth_kwargs()) as session:

    def action(page) -> None:
        page.wait_for_timeout(8000)
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(3000)

    session.fetch(URL, network_idle=True, page_action=action)
    seen = set()
    for resp in session.network.search(limit=None):
        u = resp.url
        if "tradingview" not in u:
            continue
        if u in seen:
            continue
        seen.add(u)
        if any(k in u.lower() for k in ("history", "timescale", "symbol", "quotes", "chart")):
            print(resp.status, u[:200])

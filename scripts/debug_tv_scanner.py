import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.utils import playwright_get_json

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/?timeframe=12M"
SCAN = "https://scanner.tradingview.com/bonds/scan?label-product=symbol-page"

payload = {
    "filter": [{"left": "name", "operation": "match", "right": "CN10Y"}],
    "symbols": {"query": {"types": []}, "tickers": []},
    "columns": ["close", "change", "high", "low", "open", "volume"],
    "range": [0, 1],
}


def action(page) -> None:
    result = page.context.request.post(SCAN, data=json.dumps(payload), headers={"Content-Type": "application/json"})
    print("scanner status", result.status, result.text()[:500])


with StealthySession(record_requests=True, max_recorded_requests=2000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"scanner\.tradingview\.com", limit=None):
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if text and len(text) > 20:
            print("net", resp.url[:100], len(text), text[:300])

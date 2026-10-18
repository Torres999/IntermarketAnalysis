import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import parse_investing_historical

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"
pair_id = "40820"


def action(page) -> None:
    for _ in range(15):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(800)


with StealthySession(record_requests=True, max_recorded_requests=2000, **stealth_kwargs()) as session:
    page = session.fetch(referer, network_idle=True, page_action=action)
    html = page.html_content or ""
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
    if match:
        store = json.loads(match.group(1))["props"]["pageProps"]["state"]["historicalDataStore"]
        rows = parse_investing_historical(store["historicalData"])
        print("next rows", len(rows))
    apis = 0
    total = 0
    for resp in session.network.search(url_pattern=rf"historical/{pair_id}", limit=None):
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        apis += 1
        if text:
            total += len(parse_investing_historical(json.loads(text)))
    print("api calls", apis, "parsed total", total)

import json
from datetime import date

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import (
    _rewrite_historical_url,
    parse_investing_historical,
)

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"
pair_id = "40820"
chunk_start, chunk_end = date(2024, 1, 1), date(2024, 12, 31)
captured: list[dict] = []


def handler(route) -> None:
    req = route.request
    print("route hit", req.url[:120])
    if f"historical/{pair_id}" not in req.url:
        route.continue_()
        return
    new_url = _rewrite_historical_url(req.url, chunk_start, chunk_end)
    print("rewritten", new_url[:140])
    response = route.fetch(url=new_url)
    print("fetch status", response.status, "len", len(response.text()))
    text = response.text()
    if text:
        payload = json.loads(text)
        if isinstance(payload, dict):
            captured.append(payload)
    route.fulfill(response=response)


def page_setup(page) -> None:
    page.route("**/financialdata/historical/**", handler)


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_setup=page_setup)

print("captured payloads", len(captured))
if captured:
    rows = parse_investing_historical(captured[0])
    print("rows", len(rows))

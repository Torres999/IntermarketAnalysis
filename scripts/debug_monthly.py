import json
from datetime import date

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import parse_investing_historical

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"
pair_id = "40820"
captured: list[dict] = []


def handler(route) -> None:
    req = route.request
    if f"historical/{pair_id}" not in req.url:
        route.continue_()
        return
    url = req.url.replace("time-frame=Daily", "time-frame=Monthly")
    response = route.fetch(url=url)
    print("status", response.status, "len", len(response.text()))
    text = response.text()
    if text and response.status == 200:
        payload = json.loads(text)
        if isinstance(payload, dict):
            captured.append(payload)
    route.fulfill(response=response)


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_setup=lambda p: p.route("**/financialdata/historical/**", handler))

if captured:
    rows = parse_investing_historical(captured[0])
    print("rows", len(rows), "range", rows[0][0] if rows else None, rows[-1][0] if rows else None)

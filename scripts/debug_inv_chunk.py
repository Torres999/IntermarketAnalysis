from datetime import date

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import (
    api_headers,
    historical_api_url,
    parse_investing_historical,
)

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"
url = historical_api_url("40820", date(2024, 1, 1), date(2024, 1, 31))


def action(page) -> None:
    resp = page.context.request.get(url, headers=api_headers(referer))
    text = resp.text()
    print("status", resp.status, "len", len(text))
    if text:
        rows = parse_investing_historical(__import__("json").loads(text))
        print("rows", len(rows), rows[:2])


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_action=action)

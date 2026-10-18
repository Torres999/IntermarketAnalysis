import json
from datetime import date

from scrapling.fetchers import Fetcher, StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import historical_api_url, parse_investing_historical

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"
pair_id = "40820"
url = historical_api_url(pair_id, date(2024, 1, 1), date(2024, 12, 31))
cookies_header = ""


def action(page) -> None:
    global cookies_header
    cookies = page.context.cookies()
    cookies_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_action=action)

headers = {
    "domain-id": "cn",
    "origin": "https://cn.investing.com",
    "referer": "https://cn.investing.com/",
    "accept": "*/*",
    "cookie": cookies_header,
}
resp = Fetcher.get(url, impersonate="chrome", headers=headers)
print("fetcher status", resp.status, "len", len(resp.text or ""))
if resp.text:
    rows = parse_investing_historical(json.loads(resp.text))
    print("rows", len(rows))

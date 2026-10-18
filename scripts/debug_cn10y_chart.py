import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range
from intermarket_analysis.scrapers.investing_api import parse_investing_historical, parse_sbcharts_candles

URL = "https://cn.investing.com/rates-bonds/china-10-year-bond-yield-historical-data"


def action(page) -> None:
    page.wait_for_timeout(2500)
    select_chart_range(page, "5年", wait_ms=6000)


with StealthySession(record_requests=True, max_recorded_requests=3000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"sbcharts|financialdata/historical|tvc4\.investing", limit=None):
        text = resp.body.decode("utf-8", errors="replace") if isinstance(resp.body, bytes) else str(resp.body)
        print(resp.url[:130], "len", len(text))
        if "financialdata/historical" in resp.url and text.startswith("{"):
            rows = parse_investing_historical(json.loads(text))
            print("  fin rows", len(rows), "sample", rows[:2])
        if "sbcharts" in resp.url and "_5years" in resp.url and text.startswith("{"):
            rows = parse_sbcharts_candles(json.loads(text))
            print("  sb rows", len(rows), "sample", rows[:2])
        if "tvc4.investing.com" in resp.url and "/history?" in resp.url:
            m = re.search(r"symbol=(\d+)", resp.url)
            print("  tv symbol", m.group(1) if m else None, text[:80])

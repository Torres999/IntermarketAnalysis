import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range
from intermarket_analysis.scrapers.investing_api import (
    parse_pd_instrument_candles,
    parse_sbcharts_candles,
)

URL = "https://cn.investing.com/rates-bonds/10-year-t-bond-futures-streaming-chart"


def action(page) -> None:
    page.wait_for_timeout(2500)
    try:
        select_chart_range(page, "5年", wait_ms=7000)
    except Exception as exc:
        print("click", exc)


with StealthySession(record_requests=True, max_recorded_requests=4000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"financialdata/historical/", limit=3):
        m = re.search(r"historical/(\d+)", resp.url)
        print("pair", m.group(1) if m else None, resp.url[:90])
    for resp in session.network.search(url_pattern=r"5years\.json", limit=2):
        rows = parse_sbcharts_candles(json.loads(resp.body))
        print("5y sb", len(rows), rows[0], rows[-1])
    for resp in session.network.search(url_pattern=r"charts/candles/p1m", limit=2):
        rows = parse_pd_instrument_candles(json.loads(resp.body))
        print("p1m", len(rows), rows[0], rows[-1])

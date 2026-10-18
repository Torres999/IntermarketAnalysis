import re
from datetime import date, timedelta

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range
from intermarket_analysis.scrapers.investing_api import parse_investing_historical

end = date.today()
start = end - timedelta(days=365 * 5)

for name, url in (
    ("sse", "https://cn.investing.com/indices/shanghai-composite-chart"),
    ("cn10y", "https://cn.investing.com/rates-bonds/china-10-year-bond-yield"),
):
    print("===", name, url)

    def action(page) -> None:
        select_chart_range(page, "5年")

    with StealthySession(record_requests=True, max_recorded_requests=2000, **stealth_kwargs()) as session:
        session.fetch(url, network_idle=True, page_action=action)
        for resp in session.network.search(url_pattern=r"financialdata/historical/", limit=None):
            m = re.search(r"historical/(\d+).*start-date=([^&]+).*end-date=([^&]+)", resp.url)
            body = resp.body
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            rows = parse_investing_historical(__import__("json").loads(text)) if text else []
            in_range = [r for r in rows if start <= r[0] <= end]
            print(" ", resp.url[:130])
            print(" ", "rows", len(rows), "in5y", len(in_range), "range", m.groups() if m else None)

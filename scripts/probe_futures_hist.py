import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import parse_investing_historical

URL = "https://cn.investing.com/rates-bonds/10-year-t-bond-futures-historical-data"


with StealthySession(record_requests=True, max_recorded_requests=500, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True)
    for resp in session.network.search(url_pattern=r"financialdata/historical/", limit=5):
        m = re.search(r"historical/(\d+)", resp.url)
        text = resp.body.decode("utf-8", errors="replace") if isinstance(resp.body, bytes) else str(resp.body)
        rows = parse_investing_historical(json.loads(text)) if text.startswith("{") else []
        print("pair", m.group(1) if m else None, "rows", len(rows), rows[:2] if rows else None)

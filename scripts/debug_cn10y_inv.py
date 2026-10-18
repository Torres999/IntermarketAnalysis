import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.investing.com/rates-bonds/china-10-year-bond-yield-historical-data"

with StealthySession(record_requests=True, max_recorded_requests=1000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True)
    for resp in session.network.search(url_pattern=r"financialdata/historical/", limit=None):
        m = re.search(r"historical/(\d+)", resp.url)
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        print("pair", m.group(1) if m else None, "len", len(text), resp.url[:130])

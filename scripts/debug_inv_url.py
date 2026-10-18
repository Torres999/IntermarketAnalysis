import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

urls = [
    "https://cn.investing.com/indices/shanghai-composite-historical-data?start-date=2024-01-01&end-date=2024-12-31",
    "https://cn.investing.com/indices/shanghai-composite-historical-data/40820?start-date=2024-01-01&end-date=2024-12-31",
]

for url in urls:
    with StealthySession(record_requests=True, max_recorded_requests=200, **stealth_kwargs()) as session:
        session.fetch(url, network_idle=True)
        for resp in session.network.search(url_pattern=r"financialdata/historical/40820", limit=None):
            m = re.search(r"start-date=([^&]+)", resp.url)
            body = resp.body
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            print("page", url[:80])
            print(" api", m.group(1) if m else None, "len", len(text))

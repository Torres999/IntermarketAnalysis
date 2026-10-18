import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.shanghai_index import HISTORICAL_PAGE, _parse_investing_rows

with StealthySession(record_requests=True, max_recorded_requests=1000, **stealth_kwargs()) as session:
    session.fetch(HISTORICAL_PAGE, network_idle=True)
    for resp in session.network.search(url_pattern=r"financialdata/historical", limit=None):
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        print("URL", resp.url[:120], "status", resp.status, "len", len(text))
        if text:
            try:
                payload = json.loads(text)
                rows = _parse_investing_rows(payload)
                print("parsed rows", len(rows), "sample", rows[:2])
            except json.JSONDecodeError as exc:
                print("json err", exc, text[:200])

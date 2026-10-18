import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def action(page) -> None:
    page.wait_for_timeout(18000)


with StealthySession(record_requests=True, max_recorded_requests=10000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(limit=None):
        body = resp.body
        if not body or len(body) < 100:
            continue
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if "100.6" in text or "100.679" in text:
            print("HIT", resp.url[:120], len(text))
        if '"t":' in text and '"c":' in text:
            try:
                pts = parse_tv_history(json.loads(text))
            except Exception:
                continue
            if pts and max(v for _, v in pts) > 50:
                print("HIST", resp.url[:120], len(pts), pts[0], pts[-1])

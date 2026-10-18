import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def action(page) -> None:
    page.wait_for_timeout(2500)
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(1500)
    select_chart_range(page, "5年", wait_ms=12000)


with StealthySession(record_requests=True, max_recorded_requests=8000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(limit=None):
        body = resp.body
        if not body or len(body) < 80:
            continue
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if '"t":' not in text or '"c":' not in text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        pts = parse_tv_history(payload)
        if not pts:
            continue
        sample = [v for _, v in pts[:3] + pts[-3:]]
        print(resp.url[:110])
        print("  n", len(pts), "range", pts[0], pts[-1], "sample vals", sample)

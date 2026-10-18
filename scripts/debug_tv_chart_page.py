import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.tradingview.com/chart/?symbol=TVC%3ACN10Y"
captured: list[dict] = []


def action(page) -> None:
    page.wait_for_timeout(5000)
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(2000)

    def on_response(response) -> None:
        if "/history" not in response.url:
            return
        try:
            captured.append(json.loads(response.text()))
        except Exception:
            pass

    page.on("response", on_response)
    select_chart_range(page, "5年", wait_ms=15000)
    page.wait_for_timeout(3000)


with StealthySession(record_requests=True, max_recorded_requests=8000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"history", limit=None):
        text = resp.body.decode("utf-8", errors="replace") if isinstance(resp.body, bytes) else str(resp.body or "")
        if len(text) < 40:
            continue
        print("NET", resp.url[:100], "len", len(text))
        try:
            captured.append(json.loads(text))
        except json.JSONDecodeError:
            pass

print("payloads", len(captured))
for payload in captured:
    pts = parse_tv_history(payload)
    if pts:
        print("pts", len(pts), pts[0], pts[-1], "max", max(v for _, v in pts))

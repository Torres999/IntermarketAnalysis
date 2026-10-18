import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.investing.com/indices/shanghai-composite-chart"


def action(page) -> None:
    page.wait_for_timeout(2500)
    select_chart_range(page, "5年", wait_ms=7000)


with StealthySession(record_requests=True, max_recorded_requests=3000, **stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"history\?", limit=None):
        if "tvc4.investing.com" not in resp.url:
            continue
        text = resp.body.decode("utf-8", errors="replace") if isinstance(resp.body, bytes) else str(resp.body)
        print("TV history URL", resp.url[:140])
        payload = json.loads(text)
        pts = parse_tv_history(payload)
        print(" parsed", len(pts), "sample", pts[:2], pts[-2:] if pts else [])
    for resp in session.network.search(url_pattern=r"5years\.json", limit=None):
        text = resp.body.decode("utf-8", errors="replace") if isinstance(resp.body, bytes) else str(resp.body)
        print("5years json len", len(text), resp.url)
        data = json.loads(text)
        print(" keys", list(data.keys())[:10] if isinstance(data, dict) else type(data))
        if isinstance(data, dict) and "data" in data:
            print(" data len", len(data["data"]))

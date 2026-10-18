import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"
out: list[str] = []


def action(page) -> None:
    page.wait_for_timeout(12000)
    select_quote_mode_tab(page, "价格")
    select_chart_range(page, "5年", wait_ms=10000)
    scripts = page.evaluate(
        """() => [...document.querySelectorAll('script')].map(s => s.textContent || '').filter(t => t.length > 500)"""
    )
    out.extend(scripts)


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

for i, text in enumerate(out):
    if "CN10Y" not in text and "100." not in text:
        continue
    print("script", i, "len", len(text))
    for pat in (r'"c"\s*:\s*\[[^\]]+\]', r'"points"\s*:\s*\[[^\]]+\]'):
        m = re.search(pat, text)
        if m and "100" in m.group(0):
            print(" ", m.group(0)[:300])

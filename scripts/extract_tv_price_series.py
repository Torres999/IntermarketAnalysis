import json
import re
from datetime import date, datetime, timezone

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def action(page) -> None:
    page.wait_for_timeout(12000)
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(2000)
    select_chart_range(page, "5年", wait_ms=10000)


with StealthySession(**stealth_kwargs()) as session:
    resp = session.fetch(URL, network_idle=True, page_action=action)
    html = resp.html_content or ""

idx = html.find("100.679")
print("idx", idx)
print(html[idx - 400 : idx + 400])

for pattern in (
    r'"points":\s*\[\[.*?\]\]',
    r'"series":\s*\[\{[^\]]+\]\}',
    r'"data":\s*\{"s":"ok"[^}]+\}',
):
    for m in re.finditer(pattern, html[idx - 50000 : idx + 50000] if idx >= 0 else html):
        blob = m.group(0)
        if "100" in blob:
            print("match", pattern, blob[:500])
            break

# TradingView often embeds: "prices":{"values":[...]}
for m in re.finditer(r'"values"\s*:\s*\[[^\]]{20,5000}\]', html):
    blob = m.group(0)
    if "100" in blob or re.search(r"\d{2,3}\.\d+", blob):
        nums = json.loads("{" + blob + "}")["values"]
        if nums and max(nums) > 50:
            print("values len", len(nums), "minmax", min(nums), max(nums))
            break

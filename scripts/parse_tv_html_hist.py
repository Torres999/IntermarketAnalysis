import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def action(page) -> None:
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(2000)
    select_chart_range(page, "5年", wait_ms=10000)


with StealthySession(**stealth_kwargs()) as session:
    resp = session.fetch(URL, network_idle=True, page_action=action)
    html = resp.html_content or ""

pattern = re.compile(r'\{"s":"ok","t":\[[^\]]+\],"c":\[[^\]]+\][^}]*\}')
for match in pattern.finditer(html):
    blob = match.group(0)
    if "100" not in blob and "99." not in blob:
        continue
    payload = json.loads(blob)
    pts = parse_tv_history(payload)
    print("embedded", len(pts), pts[:2], pts[-2:])
    break
else:
    idx = html.find("100.679")
    print("no embedded hist; context", html[idx - 120 : idx + 120] if idx >= 0 else "missing")

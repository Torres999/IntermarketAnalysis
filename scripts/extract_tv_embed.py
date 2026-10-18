import json
import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


extracted: dict = {}


def action(page) -> None:
    page.wait_for_timeout(2500)
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(1500)
    select_chart_range(page, "5年", wait_ms=6000)
    extracted["result"] = page.evaluate(
    """() => {
        const out = { keys: Object.keys(window).filter(k => /chart|symbol|data/i.test(k)).slice(0,30) };
        const scripts = [...document.querySelectorAll('script')].map(s => s.textContent || '').filter(t => t.includes('100.') && t.includes('CN10Y'));
        out.scriptHits = scripts.length;
        if (scripts[0]) out.sample = scripts[0].slice(0, 500);
        return out;
    }"""
    )


with StealthySession(**stealth_kwargs()) as session:
    resp = session.fetch(URL, network_idle=True, page_action=action)
    html = resp.html_content or ""

print(json.dumps(extracted.get("result", {}), ensure_ascii=False, indent=2)[:2000])

for m in re.finditer(r'"t"\s*:\s*\[[^\]]+\]', html):
    print("t array", m.group(0)[:120], "...")
    break

for m in re.finditer(r'"c"\s*:\s*\[[^\]]+\]', html):
    s = m.group(0)
    if "100" in s or "99" in s:
        print("c array", s[:200])
        break

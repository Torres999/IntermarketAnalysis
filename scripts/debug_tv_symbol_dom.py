import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_quote_mode_tab

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"
out: dict = {}


def action(page) -> None:
    page.wait_for_timeout(2000)
    for mode in ("价格", "收益率"):
        select_quote_mode_tab(page, mode)
        page.wait_for_timeout(2500)
        out[mode] = page.evaluate(
            """() => {
                const last = document.querySelector('[data-qa-id="symbol-last-value"]');
                const prs = document.querySelector('script[type="application/prs.init+json"]');
                return {
                    last: last ? last.innerText.trim() : null,
                    prs: prs ? prs.textContent.slice(0, 1200) : null,
                };
            }"""
        )


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

print(json.dumps(out, ensure_ascii=False, indent=2)[:4000])

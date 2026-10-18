from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_quote_mode_tab

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def action(page) -> None:
    page.wait_for_timeout(12000)
    for mode in ("价格", "收益率"):
        select_quote_mode_tab(page, mode)
        page.wait_for_timeout(2500)
        vals = page.evaluate(
            """() => [...document.querySelectorAll('[data-qa-id="symbol-last-value"]')].map(el => ({
                text: el.innerText.trim(),
                sym: el.closest('[data-symbol]')?.getAttribute('data-symbol') || null,
                visible: !!(el.offsetWidth || el.offsetHeight),
            }))"""
        )
        print(mode, vals)


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

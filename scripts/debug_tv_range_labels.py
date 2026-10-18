from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_quote_mode_tab

URL = "https://cn.tradingview.com/chart/?symbol=TVC%3ACN10Y"


def action(page) -> None:
    page.wait_for_timeout(8000)
    select_quote_mode_tab(page, "价格")
    labels = []
    for el in page.locator("button").all():
        try:
            t = el.inner_text().strip().replace("\n", " ")
            if t and ("5" in t or "Y" in t or "年" in t or "全部" in t or "All" in t):
                labels.append(t)
        except Exception:
            pass
    print("buttons", labels[:30])


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

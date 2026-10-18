from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"


def action(page) -> None:
    for sel in ('[class*="date" i]', '[class*="Date" i]', '[data-test*="date" i]', "input"):
        loc = page.locator(sel)
        n = loc.count()
        print(sel, n)
        for i in range(min(n, 6)):
            el = loc.nth(i)
            try:
                print(" ", i, el.evaluate("e => e.outerHTML.slice(0,120)"))
            except Exception:
                pass


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_action=action)

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"


def action(page) -> None:
    texts = []
    for el in page.locator("button").all():
        try:
            t = el.inner_text().strip()
            if t:
                texts.append(t)
        except Exception:
            pass
    print("buttons", texts[:40])


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_action=action)

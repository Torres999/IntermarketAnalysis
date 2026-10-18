import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import parse_investing_historical

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"


def action(page) -> None:
    inputs = page.locator("input").all()
    print("inputs", len(inputs))
    for i, el in enumerate(inputs[:8]):
        try:
            print(i, el.get_attribute("type"), el.get_attribute("name"), el.get_attribute("placeholder"))
        except Exception:
            pass
    # try set date fields if present
    date_inputs = page.locator('input[type="date"]')
    if date_inputs.count() >= 2:
        date_inputs.nth(0).fill("2024-01-01")
        date_inputs.nth(1).fill("2024-12-31")
        page.get_by_role("button", name=re.compile("应用|Apply|查询|Search", re.I)).first.click()
        page.wait_for_timeout(4000)


with StealthySession(record_requests=True, max_recorded_requests=500, **stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_action=action)
    for resp in session.network.search(url_pattern=r"financialdata/historical/40820", limit=None):
        m = re.search(r"start-date=([^&]+)&end-date=([^&]+)", resp.url)
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if not m:
            continue
        print("range", m.group(1), m.group(2), "len", len(text))
        if len(text) > 1000:
            rows = parse_investing_historical(__import__("json").loads(text))
            print("rows", len(rows))

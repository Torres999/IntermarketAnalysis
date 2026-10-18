import json
from datetime import date

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.investing_api import historical_api_url, parse_investing_historical

referer = "https://cn.investing.com/indices/shanghai-composite-historical-data"
url = historical_api_url("40820", date(2024, 1, 1), date(2024, 1, 31))
result: dict = {}


def action(page) -> None:
    result.update(
        page.evaluate(
            """async (url) => {
                const r = await fetch(url, {
                    credentials: 'include',
                    headers: {
                        'domain-id': 'cn',
                        'Accept': 'application/json, text/plain, */*'
                    }
                });
                const text = await r.text();
                return { status: r.status, len: text.length, text };
            }""",
            url,
        )
    )


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_action=action)

print("status", result.get("status"), "len", result.get("len"))
if result.get("status") == 200 and result.get("text"):
    rows = parse_investing_historical(json.loads(result["text"]))
    print("rows", len(rows), rows[:2])
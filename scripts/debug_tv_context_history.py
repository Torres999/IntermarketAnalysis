import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range, select_quote_mode_tab
from intermarket_analysis.scrapers.utils import parse_tv_history

URL = "https://cn.tradingview.com/chart/?symbol=TVC%3ACN10Y"
SYMBOL = "TVC:CN10Y"
end = date.today()
start = end - timedelta(days=365 * 5)
start_ts = int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp())
end_ts = int(datetime.combine(end, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc).timestamp())
result: dict = {}


def action(page) -> None:
    page.wait_for_timeout(8000)
    select_quote_mode_tab(page, "价格")
    page.wait_for_timeout(1500)
    select_chart_range(page, "5年", wait_ms=5000)
    hist_url = (
        f"https://tvc4.tradingview.com/history?symbol={quote(SYMBOL, safe='')}"
        f"&resolution=1D&from={start_ts}&to={end_ts}"
    )
    for host in (
        "https://tvc4.tradingview.com/history",
        "https://cn.tradingview.com/history",
        "https://history-data.tradingview.com/history",
    ):
        url = (
            f"{host}?symbol={quote(SYMBOL, safe='')}&resolution=1D&from={start_ts}&to={end_ts}"
        )
        try:
            resp = page.context.request.get(url)
            text = resp.text()
            result[host] = {"status": resp.status, "len": len(text), "text": text[:200]}
            if resp.ok and text:
                pts = parse_tv_history(json.loads(text))
                result[host]["pts"] = len(pts)
                if pts:
                    result[host]["sample"] = (pts[0], pts[-1])
        except Exception as exc:
            result[host] = {"error": str(exc)}


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

for host, info in result.items():
    print(host, info)

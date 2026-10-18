import json
from datetime import date, datetime, timedelta

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.browser_ui import select_chart_range

referer = "https://cn.investing.com/indices/shanghai-composite"
cutoff = date.today() - timedelta(days=365 * 5)
headers_box: dict = {}
all_pts: list[tuple[date, float]] = []


def setup(page) -> None:
    def handler(route) -> None:
        if "charts/candles/p1d" in route.request.url and "headers" not in headers_box:
            headers_box["headers"] = dict(route.request.headers)
        route.continue_()

    page.route("**/charts/candles/p1d**", handler)


def action(page) -> None:
    page.wait_for_timeout(2500)
    try:
        select_chart_range(page, "5年", wait_ms=3000)
    except Exception:
        pass
    headers = dict(headers_box.get("headers") or {})
    cookies = page.context.cookies("https://endpoints.investing.com") or page.context.cookies(
        "https://cn.investing.com"
    )
    if cookies:
        headers["cookie"] = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    cursor = None
    base = "https://endpoints.investing.com/pd-instruments/v1/instruments/40820/charts/candles/p1d?limit=500"
    for i in range(40):
        url = base if not cursor else f"{base}&cursor={cursor}"
        response = page.context.request.get(url, headers=headers)
        if response.status != 200:
            print("fail", i, response.status, response.text()[:120])
            break
        data = response.json()
        candles = data.get("candles") or []
        for item in candles:
            obs = datetime.fromisoformat(item["t"].replace("Z", "+00:00")).date()
            all_pts.append((obs, float(item["c"])))
        if not candles:
            break
        oldest = datetime.fromisoformat(candles[0]["t"].replace("Z", "+00:00")).date()
        print("page", i, "n", len(candles), "oldest", oldest)
        if oldest <= cutoff:
            break
        cursor = data.get("next_page_cursor")
        if not cursor:
            break


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(referer, network_idle=True, page_setup=setup, page_action=action)

print("total", len(all_pts))
if all_pts:
    print("range", min(all_pts)[0], max(all_pts)[0])

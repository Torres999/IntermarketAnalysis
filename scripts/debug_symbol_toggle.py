from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.tradingview.com/symbols/TVC-CN10Y/"


def read_last(page) -> str:
    loc = page.locator('[data-qa-id="symbol-last-value"]')
    if loc.count():
        return loc.first.inner_text().strip()
    return ""


def action(page) -> None:
    page.wait_for_timeout(5000)
    print("last initial", read_last(page))
    toggles = page.evaluate(
        """() => {
            const res = [];
            document.querySelectorAll('button, [role="button"], a, span, div').forEach(el => {
                const t = (el.textContent || '').replace(/\\s+/g, '');
                if (t.includes('价格') || t.includes('收益率')) {
                    res.push({tag: el.tagName, text: t.slice(0, 20), cls: String(el.className).slice(0, 60)});
                }
            });
            return res.slice(0, 30);
        }"""
    )
    print("toggles", toggles)
    for label in ("价格", "收益率"):
        loc = page.get_by_text(label, exact=True)
        print(label, "count", loc.count())
        for i in range(min(loc.count(), 3)):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    el.click(timeout=5000)
                    page.wait_for_timeout(2500)
                    print(f"  clicked {label} #{i} last={read_last(page)}")
            except Exception as exc:
                print(f"  err {exc}")


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

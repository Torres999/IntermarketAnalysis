from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.tradingview.com/chart/?symbol=TVC%3ACN10Y"


def action(page) -> None:
    page.wait_for_timeout(10000)
    hits = page.evaluate(
        """() => {
            const out = [];
            for (const el of document.querySelectorAll('button, [role="button"], span, div')) {
                const t = (el.textContent || '').trim();
                if (t === '价格' || t === '收益率') {
                    out.push({
                        tag: el.tagName,
                        text: t,
                        class: el.className?.slice?.(0, 80) || '',
                        visible: !!(el.offsetWidth || el.offsetHeight),
                    });
                }
            }
            return out.slice(0, 20);
        }"""
    )
    print("nodes", hits)
    last_before = page.locator('[data-qa-id="symbol-last-value"]').inner_text()
    print("last before", last_before)

    for sel in (
        "button:has-text('价格')",
        "[role='button']:has-text('价格')",
        "text=价格",
    ):
        loc = page.locator(sel)
        print(sel, "count", loc.count())
        if loc.count():
            try:
                loc.first.click(timeout=5000)
                page.wait_for_timeout(3000)
                last = page.locator('[data-qa-id="symbol-last-value"]').inner_text()
                print("  after click last", last)
            except Exception as exc:
                print("  click err", exc)


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.tradingview.com/chart/?symbol=TVC%3ACN10Y"


def action(page) -> None:
    page.wait_for_timeout(12000)
    frames = page.frames
    print("frames", len(frames))
    for i, frame in enumerate(frames):
        print(i, frame.url[:100] if frame.url else "main")
        try:
            hits = frame.evaluate(
                """() => {
                    const out = [];
                    for (const el of document.querySelectorAll('*')) {
                        const t = (el.textContent || '').trim();
                        if (t === '价格' || t === '收益率') out.push(el.tagName);
                        if (out.length > 10) break;
                    }
                    return out;
                }"""
            )
            if hits:
                print("  hits", hits)
        except Exception as exc:
            print("  err", str(exc)[:80])


with StealthySession(**stealth_kwargs()) as session:
    session.fetch(URL, network_idle=True, page_action=action)

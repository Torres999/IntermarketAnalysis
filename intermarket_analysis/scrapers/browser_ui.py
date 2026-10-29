from __future__ import annotations


def dismiss_investing_overlays(page) -> None:
    """Close cookie banners / regwalls that block chart clicks on cn.investing.com."""
    accept_selectors = [
        "#onetrust-accept-btn-handler",
        "#accept-recommended-btn-handler",
        "button#onetrust-accept-btn-handler",
        "button:has-text('接受全部')",
        "button:has-text('全部接受')",
        "button:has-text('接受所有')",
        "button:has-text('我同意')",
        "button:has-text('同意')",
        "button:has-text('Accept All')",
        "button:has-text('Allow All')",
    ]
    for sel in accept_selectors:
        try:
            loc = page.locator(sel).first
            if not loc.is_visible(timeout=800):
                continue
            loc.click(timeout=3000)
            page.wait_for_timeout(800)
            break
        except Exception:
            continue

    try:
        page.evaluate(
            """() => {
                for (const id of ['onetrust-consent-sdk', 'onetrust-banner-sdk', 'regwall-container']) {
                    const el = document.getElementById(id);
                    if (el) el.remove();
                }
                document.querySelectorAll('.onetrust-pc-dark-filter, .ot-fade-in').forEach((n) => n.remove());
                document.body.style.overflow = '';
            }"""
        )
    except Exception:
        pass
    page.wait_for_timeout(400)


def _chart_range_locators(page, label: str):
    data_test = {
        "5年": "ws-markets-chart-5y-btn",
        "1年": "ws-markets-chart-1y-btn",
        "6月": "ws-markets-chart-6m-btn",
        "3月": "ws-markets-chart-3m-btn",
        "1月": "ws-markets-chart-1m-btn",
        "最大值": "ws-markets-chart-max-btn",
    }
    dt = data_test.get(label)
    locators = []
    if dt:
        locators.append(("data_test", page.locator(f'[data-test="{dt}"]')))
    locators.extend(
        [
            ("role_button", page.get_by_role("button", name=label, exact=True)),
            ("button_text", page.locator(f"button:has-text('{label}')")),
            ("span_text", page.locator(f"span:has-text('{label}')")),
            ("text", page.get_by_text(label, exact=True)),
        ]
    )
    return locators


def select_chart_range(page, label: str = "5年", *, wait_ms: int = 3500) -> None:
    """Click Investing / TradingView bottom timeframe button (e.g. 5年)."""
    dismiss_investing_overlays(page)
    last_error: Exception | None = None
    for _name, locator in _chart_range_locators(page, label):
        try:
            count = locator.count()
            if count == 0:
                continue
            for i in range(min(count, 5)):
                el = locator.nth(i)
                if not el.is_visible():
                    continue
                el.scroll_into_view_if_needed(timeout=5000)
                try:
                    el.click(timeout=8000)
                except Exception:
                    dismiss_investing_overlays(page)
                    el.click(timeout=8000, force=True)
                page.wait_for_timeout(wait_ms)
                return
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Could not click chart range '{label}': {last_error}")


def select_quote_mode_tab(page, label: str = "价格") -> None:
    """Switch chart between 收益率 and 价格 (TradingView / Investing)."""
    dismiss_investing_overlays(page)
    locators = [
        page.get_by_role("button", name=label, exact=True),
        page.get_by_text(label, exact=True),
    ]
    for loc in locators:
        try:
            count = loc.count()
            for i in range(min(count, 4)):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                el.scroll_into_view_if_needed(timeout=5000)
                el.click(timeout=5000)
                page.wait_for_timeout(2000)
                return
        except Exception:
            continue
    try:
        page.evaluate(
            """(label) => {
                const nodes = [...document.querySelectorAll('button, [role="button"], span, div, a')];
                for (const el of nodes) {
                    const text = (el.textContent || '').replace(/\\s+/g, '');
                    if (text !== label && !(text.includes(label) && text.length <= label.length + 2)) {
                        continue;
                    }
                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    return true;
                }
                return false;
            }""",
            label,
        )
        page.wait_for_timeout(2000)
    except Exception:
        pass


def select_tradingview_yield_tab(page) -> None:
    select_quote_mode_tab(page, "收益率")

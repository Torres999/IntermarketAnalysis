from __future__ import annotations


def select_chart_range(page, label: str = "5年", *, wait_ms: int = 6500) -> None:
    """Click Investing / TradingView bottom timeframe button (e.g. 5年)."""
    selectors = [
        ("role_button", page.get_by_role("button", name=label, exact=True)),
        ("button_text", page.locator(f"button:has-text('{label}')")),
        ("span_text", page.locator(f"span:has-text('{label}')")),
        ("text", page.get_by_text(label, exact=True)),
    ]
    last_error: Exception | None = None
    for _name, locator in selectors:
        try:
            count = locator.count()
            if count == 0:
                continue
            for i in range(min(count, 5)):
                el = locator.nth(i)
                if not el.is_visible():
                    continue
                el.scroll_into_view_if_needed(timeout=5000)
                el.click(timeout=8000)
                page.wait_for_timeout(wait_ms)
                return
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Could not click chart range '{label}': {last_error}")


def select_quote_mode_tab(page, label: str = "价格") -> None:
    """Switch chart between 收益率 and 价格 (TradingView / Investing)."""
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

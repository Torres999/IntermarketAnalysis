from __future__ import annotations

import os


def stealth_kwargs(**overrides: object) -> dict[str, object]:
    """Browser options for Scrapling stealth fetchers (env-tunable)."""
    real_chrome = os.environ.get("INTERMARKET_REAL_CHROME", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    headless = os.environ.get("INTERMARKET_HEADLESS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    opts: dict[str, object] = {"headless": headless, "real_chrome": real_chrome}
    opts.update(overrides)
    return opts

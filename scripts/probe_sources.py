"""Temporary probe script for data source APIs."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone

from scrapling.fetchers import Fetcher, StealthyFetcher


def probe_chinamoney() -> None:
    url = "https://www.chinamoney.com.cn/chinese/bkrmbidx/"
    page = Fetcher.get(url, impersonate="chrome")
    print("chinamoney html len", len(page.text))
    for pat in (
        r"/r/cms/[^\"']+",
        r"bkrmb[^\"']*",
        r"\.json[^\"']*",
        r"getData[^\"']*",
    ):
        hits = set(re.findall(pat, page.text, re.I))
        if hits:
            print("pattern", pat, "sample", list(hits)[:8])

    api_candidates = [
        "https://www.chinamoney.com.cn/r/cms/www/chinese/ywgg/json/bkrmbidx/bkrmbidx.json",
        "https://www.chinamoney.com.cn/r/cms/www/chinese/ywgg/json/bkrmbidx/bkrmbidx_his.json",
    ]
    for api in api_candidates:
        try:
            r = Fetcher.get(api, impersonate="chrome")
            print("api", api, "status", r.status, "len", len(r.text))
            print(r.text[:300])
        except Exception as exc:
            print("api fail", api, exc)


def probe_tradingview() -> None:
    symbol = "TVC:CN10Y"
    now = int(datetime.now(tz=timezone.utc).timestamp())
    start = now - 5 * 365 * 24 * 3600
    urls = [
        f"https://symbol-search.tradingview.com/symbol_search/?text=CN10Y&hl=1",
        f"https://tvc4.tradingview.com/history?symbol={symbol}&resolution=1M&from={start}&to={now}",
    ]
    for url in urls:
        try:
            r = Fetcher.get(url, impersonate="chrome")
            print("tv", url[:80], "len", len(r.text), "head", r.text[:200])
        except Exception as exc:
            print("tv fail", url[:80], exc)


def probe_investing() -> None:
    # Shanghai Composite instrument id on investing.com is often 40849
    url = "https://cn.investing.com/indices/shanghai-composite-historical-data"
    try:
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        print("investing html len", len(page.html_content))
        for pat in (r"historicalData[^\"']*", r"/api/financialdata/[^\"']+"):
            hits = set(re.findall(pat, page.html_content or "", re.I))
            if hits:
                print("investing pattern", list(hits)[:5])
    except Exception as exc:
        print("investing stealth fail", exc)


if __name__ == "__main__":
    fn = sys.argv[1] if len(sys.argv) > 1 else "all"
    if fn in ("all", "cn"):
        probe_chinamoney()
    if fn in ("all", "tv"):
        probe_tradingview()
    if fn in ("all", "inv"):
        probe_investing()

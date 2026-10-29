"""Probe commodity data sources (Eastmoney kline vs Investing)."""
from __future__ import annotations

import json
import re

from scrapling.fetchers import Fetcher

SECIDS = [
    ("au_main", "113.au888"),
    ("au_main2", "113.au9999"),
    ("sc_main", "113.sc888"),
    ("rb_main", "113.rb888"),
    ("nhci_inv", None),
]

EM_URL = (
    "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    "?fields1=f1&fields2=f51,f52&fqt=1&klt=101&lmt=500"
    "&secid={secid}&beg=20230101&end=20261231"
)


def probe_eastmoney(secid: str) -> None:
    url = EM_URL.format(secid=secid)
    r = Fetcher.get(url, impersonate="chrome", timeout=25)
    data = json.loads(r.text)
    klines = (data.get("data") or {}).get("klines") or []
    print("eastmoney", secid, "n=", len(klines), "sample=", klines[:1], klines[-1:] if klines else [])


if __name__ == "__main__":
    for name, secid in SECIDS:
        if not secid:
            continue
        try:
            probe_eastmoney(secid)
        except Exception as exc:
            print("eastmoney fail", name, exc)

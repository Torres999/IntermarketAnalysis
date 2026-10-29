import json
import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.eastmoney.com/"}


def kline(secid: str) -> None:
    url = (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?fields1=f1&fields2=f51,f52&fqt=1&klt=101&lmt=5&secid={secid}"
        "&beg=20250901&end=20251029"
    )
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20).read()
    data = json.loads(raw)
    k = (data.get("data") or {}).get("klines") or []
    print("kline", secid, "rc", data.get("rc"), "n", len(k), k[:1])


def page(code: str) -> None:
    url = f"https://quote.eastmoney.com/qihuo/{code}.html"
    html = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20).read().decode(
        "utf-8", "replace"
    )
    for pat in (r'"secid"\s*:\s*"([^"]+)"', r"secid=(\d+\.\w+)", r"quoteCode\s*:\s*'([^']+)'"):
        hits = set(re.findall(pat, html))
        if hits:
            print("page", code, pat, list(hits)[:5])


for c in ("au888", "sc888", "cu888", "rb888"):
    page(c)

for secid in ("113.AU888", "114.AU888", "115.AU888", "142.AU888", "225.au888"):
    kline(secid)

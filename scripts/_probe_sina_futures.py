import json
import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}


def sina_daily(symbol: str) -> None:
    url = (
        "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
        f"var=/InnerFuturesNewService.getDailyKLine?symbol={symbol}"
    )
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25).read().decode(
        "utf-8", "replace"
    )
    m = re.search(r"\((\[.*\])\)", raw, re.S)
    if not m:
        print("sina", symbol, "parse fail", raw[:120])
        return
    rows = json.loads(m.group(1))
    print("sina", symbol, "n", len(rows), "head", rows[0] if rows else None, "tail", rows[-1] if rows else None)


for sym in ("AU0", "SC0", "CU0", "RB0", "I0", "M0"):
    try:
        sina_daily(sym)
    except Exception as exc:
        print("sina fail", sym, exc)

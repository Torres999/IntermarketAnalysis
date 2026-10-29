"""Check Investing.cn chart page URLs (HTTP status)."""
from scrapling.fetchers import Fetcher

URLS = {
    "cn10y_yield_a": "https://cn.investing.com/rates-bonds/china-10-year-bond-yield",
    "cn10y_yield_b": "https://cn.investing.com/rates-bonds/china-10-year-bond-yield-chart",
    "sse50_a": "https://cn.investing.com/indices/sse-50",
    "sse50_b": "https://cn.investing.com/indices/sse-50-index",
    "sse50_c": "https://cn.investing.com/indices/shanghai-stock-exchange-50-index",
    "csi300_a": "https://cn.investing.com/indices/csi-300",
    "csi300_b": "https://cn.investing.com/indices/csi-300-chart",
    "csi500_a": "https://cn.investing.com/indices/csi-500",
    "csi1000_a": "https://cn.investing.com/indices/csi-1000",
    "future_if_a": "https://cn.investing.com/indices/china-300-index-futures",
    "future_if_b": "https://cn.investing.com/indices/china-300-index-futures-chart",
    "star50_a": "https://cn.investing.com/indices/star-50",
    "star50_b": "https://cn.investing.com/indices/star-50-index",
}

for name, url in URLS.items():
    try:
        r = Fetcher.get(url, impersonate="chrome", timeout=15, allow_redirects=True)
        print(name, r.status, url.split("/")[-1])
    except Exception as e:
        print(name, "ERR", e)

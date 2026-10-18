import re

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.investing.com/indices/shanghai-composite"

with StealthySession(**stealth_kwargs()) as session:
    page = session.fetch(URL, network_idle=True)
    html = page.html_content or ""

path = __file__.replace("scripts\\debug_investing.py", "data\\inv_debug.html").replace(
    "scripts/debug_investing.py", "data/inv_debug.html"
)
with open(path, "w", encoding="utf-8") as f:
    f.write(html)

patterns = [
    r'data-pair-id="(\d+)"',
    r'"pairId"\s*:\s*(\d+)',
    r"instrumentId\s*[:=]\s*(\d+)",
    r'"instrument_id"\s*:\s*(\d+)',
    r"financialdata/historical/(\d+)",
    r"sedol\s*:\s*'[^']*'\s*,\s*id\s*:\s*(\d+)",
]
for pat in patterns:
    hits = sorted(set(re.findall(pat, html)))
    if hits:
        print(pat, hits[:20])

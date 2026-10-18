from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs

URL = "https://cn.investing.com/indices/shanghai-composite-historical-data"
with StealthySession(**stealth_kwargs()) as session:
    page = session.fetch(URL, network_idle=True)
    html = page.html_content or ""
open(r"G:\youtube\IntermarketAnalysis\data\hist_debug.html", "w", encoding="utf-8").write(html)
print("len", len(html))

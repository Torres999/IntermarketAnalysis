import json
import re
from pathlib import Path

html = Path(__file__).resolve().parents[1].joinpath("data", "hist_debug.html").read_text(encoding="utf-8")
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
data = json.loads(match.group(1))
store = data["props"]["pageProps"]["state"]["historicalDataStore"]
print(json.dumps(store, ensure_ascii=False, indent=2)[:4000])

import json
import re
from pathlib import Path

html = Path(__file__).resolve().parents[1].joinpath("data", "hist_debug.html").read_text(encoding="utf-8")
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
data = json.loads(match.group(1))
hist = data["props"]["pageProps"]["state"]["historicalDataStore"]
print("historicalDataStore keys:", list(hist.keys())[:30])
for k, v in hist.items():
    if isinstance(v, list):
        print(k, "list len", len(v), "sample keys", list(v[0].keys())[:8] if v else None)
    elif isinstance(v, dict):
        print(k, "dict keys", list(v.keys())[:10])

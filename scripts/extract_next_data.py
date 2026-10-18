import json
import re
from pathlib import Path

html = Path(__file__).resolve().parents[1].joinpath("data", "inv_debug.html").read_text(encoding="utf-8")
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    print("no __NEXT_DATA__")
    raise SystemExit(1)
data = json.loads(match.group(1))

def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k in ("pairId", "instrument_id", "instrumentId", "pair_id", "id") and isinstance(v, int):
                if v > 0:
                    print(p, v)
            walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:50]):
            walk(v, f"{path}[{i}]")

walk(data)

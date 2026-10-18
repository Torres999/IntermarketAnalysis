import re
from pathlib import Path

html = Path(__file__).resolve().parents[1].joinpath("data", "hist_debug.html").read_text(encoding="utf-8")
tests = sorted(set(re.findall(r'data-test="([^"]+)"', html)))
for t in tests:
    if any(k in t.lower() for k in ("hist", "date", "range", "download", "export", "table", "picker")):
        print(t)

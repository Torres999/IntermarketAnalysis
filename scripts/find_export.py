import re
from pathlib import Path

html = Path(__file__).resolve().parents[1].joinpath("data", "hist_debug.html").read_text(encoding="utf-8")
for word in ("download", "Download", "export", "Export", "Excel", "csv", "CSV", "下载"):
    if word in html:
        print("found", word)
for m in re.finditer(r'data-test="([^"]*(?:download|export|excel|csv)[^"]*)"', html, re.I):
    print("data-test", m.group(1))

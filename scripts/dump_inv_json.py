import json

from scrapling.fetchers import StealthySession

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.shanghai_index import HISTORICAL_PAGE

out = __file__.replace("scripts\\dump_inv_json.py", "data\\inv_api_sample.json").replace(
    "scripts/dump_inv_json.py", "data/inv_api_sample.json"
)

with StealthySession(record_requests=True, max_recorded_requests=1000, **stealth_kwargs()) as session:
    session.fetch(HISTORICAL_PAGE, network_idle=True)
    for resp in session.network.search(url_pattern=r"financialdata/historical/40820", limit=None):
        body = resp.body
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if not text:
            continue
        payload = json.loads(text)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("saved", out, "keys", payload.keys() if isinstance(payload, dict) else type(payload))

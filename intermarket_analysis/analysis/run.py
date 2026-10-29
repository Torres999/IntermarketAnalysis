from __future__ import annotations

from datetime import date

from intermarket_analysis.analysis.regimes import assess_four_leg_sync
from intermarket_analysis.analysis.smt import detect_index_smt_events, future_spot_spread_summary
from intermarket_analysis.config import SERIES, default_start
from intermarket_analysis.storage import query_series

BROAD_INDEX_IDS = ["csi300", "sse_composite", "chinext", "szse_component"]
FUTURE_SPOT_PAIRS = [
    ("future_if", "csi300"),
    ("future_ih", "sse50"),
    ("future_ic", "csi500"),
    ("future_im", "csi1000"),
]


def run_analysis(
    start: date | None = None,
    end: date | None = None,
) -> dict[str, object]:
    end = end or date.today()
    start = start or default_start(end)

    needed = set(BROAD_INDEX_IDS)
    needed.update(
        [
            "cn10y_yield",
            "rmb_cfets",
            "nh_commodity",
            "comm_au",
            "comm_sc",
        ]
    )
    for fut, spot in FUTURE_SPOT_PAIRS:
        needed.add(fut)
        needed.add(spot)
    data = query_series(sorted(needed), start, end)

    sync = assess_four_leg_sync(data)
    smt_events = detect_index_smt_events(data, BROAD_INDEX_IDS)
    spreads = [
        future_spot_spread_summary(data, fut, spot) for fut, spot in FUTURE_SPOT_PAIRS
    ]

    missing = [sid for sid in needed if not data.get(sid)]
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "four_leg_sync": sync,
        "three_leg_sync": sync,
        "index_smt_events": smt_events[:12],
        "future_spot_spreads": spreads,
        "missing_series": missing,
        "series_catalog_count": len(SERIES),
    }

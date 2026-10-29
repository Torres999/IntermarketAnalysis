"""Resolve Investing.com pair IDs for series in config (requires browser/network)."""
from __future__ import annotations

import argparse

from intermarket_analysis.config import SERIES
from intermarket_analysis.scrapers.investing_api import resolve_pair_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover Investing pair_id values")
    parser.add_argument(
        "--scraper",
        choices=("investing_chart", "all"),
        default="investing_chart",
    )
    args = parser.parse_args()

    for spec in SERIES.values():
        if spec.scraper != "investing_chart" and args.scraper != "all":
            continue
        if not spec.enabled:
            continue
        pid = resolve_pair_id(spec.source_url, default=spec.default_pair_id or "0")
        print(
            f"{spec.series_id:18} default={spec.default_pair_id or '-':8} resolved={pid:8}  {spec.source_url}"
        )


if __name__ == "__main__":
    main()

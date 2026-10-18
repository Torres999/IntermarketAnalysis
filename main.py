from __future__ import annotations

import argparse

from intermarket_analysis.pipeline import run_backfill_chart_series, run_incremental_scrape
from intermarket_analysis.server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="Intermarket analysis scraper & dashboard")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scrape", help="Run incremental scrape for all series")
    sub.add_parser(
        "backfill-charts",
        help="Clear and re-scrape SSE & CN10Y via 5Y chart button (Investing/TradingView)",
    )
    serve_p = sub.add_parser("serve", help="Start local dashboard web server")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)

    run_p = sub.add_parser("run", help="Scrape then start dashboard")
    run_p.add_argument("--host", default="127.0.0.1")
    run_p.add_argument("--port", type=int, default=8765)

    args = parser.parse_args()
    if args.command == "scrape":
        summary = run_incremental_scrape()
        print(summary)
    elif args.command == "backfill-charts":
        summary = run_backfill_chart_series()
        print(summary)
    elif args.command == "serve":
        serve(args.host, args.port)
    elif args.command == "run":
        summary = run_incremental_scrape()
        print(summary)
        serve(args.host, args.port)


if __name__ == "__main__":
    main()

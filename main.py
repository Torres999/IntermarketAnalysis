from __future__ import annotations

import argparse
import json
import threading
import webbrowser

from intermarket_analysis.config import bootstrap_env
from intermarket_analysis.analysis.run import run_analysis
from intermarket_analysis.pipeline import (
    bootstrap_if_empty,
    run_backfill_chart_series,
    run_incremental_scrape,
)
from intermarket_analysis.server import serve


def _open_browser(host: str, port: int, delay: float = 1.2) -> None:
    if host not in ("127.0.0.1", "localhost", "0.0.0.0"):
        return
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(delay, lambda: webbrowser.open(url)).start()


def main() -> None:
    bootstrap_env()
    parser = argparse.ArgumentParser(description="Intermarket analysis scraper & dashboard")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scrape", help="Run incremental scrape for all series")
    sub.add_parser(
        "backfill-charts",
        help="Clear and re-scrape chart-based series (Investing 5Y + CN10Y)",
    )
    analyze_p = sub.add_parser("analyze", help="Run A-share multi-asset analysis summary")
    analyze_p.add_argument("--from", dest="from_date", metavar="DATE")
    analyze_p.add_argument("--to", dest="to_date", metavar="DATE")

    start_p = sub.add_parser(
        "start",
        help="Update data (incremental), open browser, start dashboard",
    )
    start_p.add_argument("--host", default="127.0.0.1")
    start_p.add_argument("--port", type=int, default=8765)
    start_p.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Start dashboard only (no data update)",
    )
    start_p.add_argument(
        "--full-backfill",
        action="store_true",
        help="Clear chart series and re-fetch 5Y before serve (first-time)",
    )

    serve_p = sub.add_parser("serve", help="Start local dashboard web server")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)

    run_p = sub.add_parser("run", help="Same as start (scrape + dashboard + browser)")
    run_p.add_argument("--host", default="127.0.0.1")
    run_p.add_argument("--port", type=int, default=8765)
    run_p.add_argument("--skip-scrape", action="store_true")
    run_p.add_argument("--full-backfill", action="store_true")

    args = parser.parse_args()
    if args.command == "scrape":
        summary = run_incremental_scrape()
        print(summary)
    elif args.command == "backfill-charts":
        summary = run_backfill_chart_series()
        print(summary)
    elif args.command == "analyze":
        from datetime import date

        start = date.fromisoformat(args.from_date) if args.from_date else None
        end = date.fromisoformat(args.to_date) if args.to_date else None
        print(json.dumps(run_analysis(start, end), ensure_ascii=False, indent=2))
    elif args.command in ("start", "run"):
        if not args.skip_scrape:
            if args.full_backfill:
                print("Running full chart backfill (may take several minutes)...")
                summary = run_backfill_chart_series()
            else:
                boot = bootstrap_if_empty()
                if boot.get("bootstrap") == "backfill_charts":
                    print("First run: backfilling chart series...")
                    summary = boot
                else:
                    print("Updating market data (incremental)...")
                    summary = run_incremental_scrape()
            print(summary)
        _open_browser(args.host, args.port)
        serve(args.host, args.port)
    elif args.command == "serve":
        serve(args.host, args.port)


if __name__ == "__main__":
    main()

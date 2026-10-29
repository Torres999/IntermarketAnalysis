"""Audit observation ranges and price jumps in market.db."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "market.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    print("series_id           n    min          max          jumps>30%")
    for row in conn.execute(
        "SELECT series_id, COUNT(*) n, MIN(value) mn, MAX(value) mx "
        "FROM observations GROUP BY series_id ORDER BY series_id"
    ):
        sid = row["series_id"]
        jumps = 0
        prev = None
        for r in conn.execute(
            "SELECT value FROM observations WHERE series_id=? ORDER BY obs_date", (sid,)
        ):
            v = r[0]
            if prev and prev > 0 and (v / prev > 1.3 or prev / v > 1.3):
                jumps += 1
            prev = v
        flag = " ***" if jumps > 5 else ""
        print(f"{sid:18} {row['n']:4} {row['mn']:12.2f} {row['mx']:12.2f} {jumps:4}{flag}")
    conn.close()


if __name__ == "__main__":
    main()

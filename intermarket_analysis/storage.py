from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from intermarket_analysis.config import DB_PATH, SERIES, SeriesSpec


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS series_meta (
                series_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                unit TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS observations (
                series_id TEXT NOT NULL,
                obs_date TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (series_id, obs_date),
                FOREIGN KEY (series_id) REFERENCES series_meta(series_id)
            );
            CREATE TABLE IF NOT EXISTS crawl_state (
                series_id TEXT PRIMARY KEY,
                last_obs_date TEXT,
                last_success_at TEXT,
                last_error TEXT,
                FOREIGN KEY (series_id) REFERENCES series_meta(series_id)
            );
            CREATE INDEX IF NOT EXISTS idx_obs_series_date ON observations(series_id, obs_date);
            """
        )
        for spec in SERIES.values():
            conn.execute(
                """
                INSERT INTO series_meta (series_id, name, source_url, unit)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(series_id) DO UPDATE SET
                    name = excluded.name,
                    source_url = excluded.source_url,
                    unit = excluded.unit
                """,
                (spec.series_id, spec.name, spec.source_url, spec.unit),
            )
        _migrate_cn10y_yield_archive(conn)


def _migrate_cn10y_yield_archive(conn: sqlite3.Connection) -> None:
    """One-time copy of legacy yield rows from cn10y into cn10y_yield."""
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM observations WHERE series_id = 'cn10y_yield'"
    ).fetchone()
    if row and row["c"]:
        return
    conn.execute(
        """
        INSERT OR IGNORE INTO observations (series_id, obs_date, value)
        SELECT 'cn10y_yield', obs_date, value
        FROM observations
        WHERE series_id = 'cn10y' AND value < 15
        """
    )


@contextmanager
def connect(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_last_obs_date(series_id: str, db_path: Path = DB_PATH) -> date | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT last_obs_date FROM crawl_state WHERE series_id = ?",
            (series_id,),
        ).fetchone()
        if row and row["last_obs_date"]:
            return date.fromisoformat(row["last_obs_date"])
        row = conn.execute(
            "SELECT MAX(obs_date) AS max_date FROM observations WHERE series_id = ?",
            (series_id,),
        ).fetchone()
        if row and row["max_date"]:
            return date.fromisoformat(row["max_date"])
    return None


def upsert_observations(
    series_id: str,
    points: Iterable[tuple[date, float]],
    db_path: Path = DB_PATH,
) -> int:
    rows = [(series_id, d.isoformat(), float(v)) for d, v in points]
    if not rows:
        return 0
    with connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO observations (series_id, obs_date, value)
            VALUES (?, ?, ?)
            ON CONFLICT(series_id, obs_date) DO UPDATE SET value = excluded.value
            """,
            rows,
        )
        max_date = max(r[1] for r in rows)
        conn.execute(
            """
            INSERT INTO crawl_state (series_id, last_obs_date, last_success_at, last_error)
            VALUES (?, ?, ?, NULL)
            ON CONFLICT(series_id) DO UPDATE SET
                last_obs_date = excluded.last_obs_date,
                last_success_at = excluded.last_success_at,
                last_error = NULL
            """,
            (series_id, max_date, _utc_now_iso()),
        )
    return len(rows)


def record_error(series_id: str, message: str, db_path: Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO crawl_state (series_id, last_error, last_success_at)
            VALUES (?, ?, ?)
            ON CONFLICT(series_id) DO UPDATE SET last_error = excluded.last_error
            """,
            (series_id, message[:2000], _utc_now_iso()),
        )


def query_series(
    series_ids: list[str],
    start: date | None,
    end: date | None,
    db_path: Path = DB_PATH,
) -> dict[str, list[dict[str, object]]]:
    if not series_ids:
        return {}
    placeholders = ",".join("?" for _ in series_ids)
    clauses = [f"series_id IN ({placeholders})"]
    params: list[object] = list(series_ids)
    if start:
        clauses.append("obs_date >= ?")
        params.append(start.isoformat())
    if end:
        clauses.append("obs_date <= ?")
        params.append(end.isoformat())
    sql = f"""
        SELECT series_id, obs_date, value
        FROM observations
        WHERE {' AND '.join(clauses)}
        ORDER BY series_id, obs_date
    """
    out: dict[str, list[dict[str, object]]] = {sid: [] for sid in series_ids}
    with connect(db_path) as conn:
        for row in conn.execute(sql, params):
            out[row["series_id"]].append(
                {"date": row["obs_date"], "value": row["value"]}
            )
    return out


def clear_series_data(series_ids: list[str], db_path: Path = DB_PATH) -> None:
    if not series_ids:
        return
    placeholders = ",".join("?" for _ in series_ids)
    with connect(db_path) as conn:
        conn.execute(
            f"DELETE FROM observations WHERE series_id IN ({placeholders})",
            series_ids,
        )
        conn.execute(
            f"DELETE FROM crawl_state WHERE series_id IN ({placeholders})",
            series_ids,
        )


def list_series_meta(db_path: Path = DB_PATH) -> list[SeriesSpec]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT series_id, name, source_url, unit FROM series_meta ORDER BY series_id"
        ).fetchall()
    return [
        SeriesSpec(
            series_id=r["series_id"],
            name=r["name"],
            source_url=r["source_url"],
            unit=r["unit"] or "",
        )
        for r in rows
    ]

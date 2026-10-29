from __future__ import annotations

from datetime import date


def to_value_map(rows: list[dict[str, object]]) -> dict[date, float]:
    out: dict[date, float] = {}
    for row in rows:
        d = date.fromisoformat(str(row["date"]))
        out[d] = float(row["value"])
    return out


def align_dates(series: dict[str, dict[date, float]]) -> list[date]:
    if not series:
        return []
    common = None
    for values in series.values():
        keys = set(values.keys())
        common = keys if common is None else common & keys
    return sorted(common or [])


def pct_returns(values: dict[date, float], dates: list[date]) -> list[float | None]:
    out: list[float | None] = [None]
    for i in range(1, len(dates)):
        prev, cur = values.get(dates[i - 1]), values.get(dates[i])
        if prev is None or cur is None or prev == 0:
            out.append(None)
        else:
            out.append((cur - prev) / prev)
    return out


def index_base100(values: dict[date, float], dates: list[date]) -> list[float | None]:
    if not dates:
        return []
    base = values.get(dates[0])
    if base is None or base == 0:
        return [None] * len(dates)
    return [(values[d] / base) * 100.0 if values.get(d) is not None else None for d in dates]


def rolling_sum(values: list[float | None], window: int) -> float | None:
    tail = [v for v in values[-window:] if v is not None]
    if len(tail) < window:
        return None
    return sum(tail)


def direction_label(window_return: float | None, *, deadband: float = 0.002) -> str:
    if window_return is None:
        return "unknown"
    if window_return > deadband:
        return "up"
    if window_return < -deadband:
        return "down"
    return "flat"

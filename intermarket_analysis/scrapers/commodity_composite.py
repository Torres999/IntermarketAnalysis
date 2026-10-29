from __future__ import annotations

from datetime import date

from intermarket_analysis.storage import query_series, upsert_observations

NH_COMPONENTS = ("comm_au", "comm_cu", "comm_sc", "comm_rb")


def build_nh_commodity_proxy(
    start: date | None,
    end: date | None,
) -> list[tuple[date, float]]:
    """Equal-weight base-100 blend of main domestic futures (Sina continuous)."""
    data = query_series(list(NH_COMPONENTS), start, end)
    if any(not data.get(sid) for sid in NH_COMPONENTS):
        return []

    maps: dict[str, dict[date, float]] = {}
    for sid in NH_COMPONENTS:
        maps[sid] = {
            date.fromisoformat(str(p["date"])): float(p["value"]) for p in data[sid]
        }

    common = sorted(set.intersection(*(set(m.keys()) for m in maps.values())))
    if not common:
        return []

    base_date = common[0]
    bases = {sid: maps[sid][base_date] for sid in NH_COMPONENTS}
    if any(b == 0 for b in bases.values()):
        return []

    out: list[tuple[date, float]] = []
    for obs in common:
        indexed = [(maps[sid][obs] / bases[sid]) * 100.0 for sid in NH_COMPONENTS]
        out.append((obs, sum(indexed) / len(indexed)))
    return out


def refresh_nh_commodity_proxy(start: date | None = None, end: date | None = None) -> int:
    points = build_nh_commodity_proxy(start, end)
    if not points:
        return 0
    return upsert_observations("nh_commodity", points)

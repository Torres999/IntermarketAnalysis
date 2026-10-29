from __future__ import annotations

from datetime import date

from intermarket_analysis.analysis.normalize import to_value_map


def _local_extrema(dates: list[date], values: list[float | None], window: int = 5):
    highs: list[tuple[date, float]] = []
    lows: list[tuple[date, float]] = []
    for i in range(window, len(dates) - window):
        v = values[i]
        if v is None:
            continue
        seg = [values[j] for j in range(i - window, i + window + 1) if values[j] is not None]
        if not seg:
            continue
        if v >= max(seg):
            highs.append((dates[i], v))
        if v <= min(seg):
            lows.append((dates[i], v))
    return highs, lows


def detect_index_smt_events(
    data: dict[str, list[dict[str, object]]],
    series_ids: list[str],
    *,
    window: int = 5,
    lookback_events: int = 8,
) -> list[dict[str, object]]:
    """Daily simplified SMT: one index fails to confirm a swing vs peers."""
    maps = {sid: to_value_map(data.get(sid) or []) for sid in series_ids}
    dates = sorted(set().union(*(m.keys() for m in maps.values())))
    if len(dates) < window * 3:
        return []

    series_vals = {
        sid: [maps[sid].get(d) for d in dates] for sid in series_ids if maps[sid]
    }
    active_ids = list(series_vals.keys())
    if len(active_ids) < 2:
        return []

    events: list[dict[str, object]] = []
    for sid in active_ids:
        highs, lows = _local_extrema(dates, series_vals[sid], window=window)
        for obs_date, _ in highs[-lookback_events:]:
            idx = dates.index(obs_date)
            peer_higher = 0
            self_failed = 0
            for other in active_ids:
                if other == sid:
                    continue
                ov = series_vals[other][idx]
                sv = series_vals[sid][idx]
                if ov is None or sv is None:
                    continue
                recent_other = [x for x in series_vals[other][max(0, idx - window) : idx + 1] if x]
                recent_self = [x for x in series_vals[sid][max(0, idx - window) : idx + 1] if x]
                if not recent_other or not recent_self:
                    continue
                if max(recent_other) > max(recent_self) * 1.001:
                    peer_higher += 1
                if sv < max(recent_self) * 0.999:
                    self_failed += 1
            if peer_higher >= 1 and self_failed >= 1:
                events.append(
                    {
                        "date": obs_date.isoformat(),
                        "kind": "bearish_smt_high",
                        "leader": sid,
                        "peers": [x for x in active_ids if x != sid],
                    }
                )

        for obs_date, _ in lows[-lookback_events:]:
            idx = dates.index(obs_date)
            peer_lower = 0
            self_failed = 0
            for other in active_ids:
                if other == sid:
                    continue
                sv = series_vals[sid][idx]
                ov = series_vals[other][idx]
                if ov is None or sv is None:
                    continue
                recent_other = [x for x in series_vals[other][max(0, idx - window) : idx + 1] if x]
                recent_self = [x for x in series_vals[sid][max(0, idx - window) : idx + 1] if x]
                if not recent_other or not recent_self:
                    continue
                if min(recent_other) < min(recent_self) * 0.999:
                    peer_lower += 1
                if sv > min(recent_self) * 1.001:
                    self_failed += 1
            if peer_lower >= 1 and self_failed >= 1:
                events.append(
                    {
                        "date": obs_date.isoformat(),
                        "kind": "bullish_smt_low",
                        "leader": sid,
                        "peers": [x for x in active_ids if x != sid],
                    }
                )

    dedup: dict[tuple[str, str, str], dict[str, object]] = {}
    for ev in events:
        key = (str(ev["date"]), str(ev["kind"]), str(ev["leader"]))
        dedup[key] = ev
    return sorted(dedup.values(), key=lambda e: str(e["date"]), reverse=True)


def future_spot_spread_summary(
    data: dict[str, list[dict[str, object]]],
    future_id: str,
    spot_id: str,
    *,
    window: int = 20,
) -> dict[str, object]:
    fmap = to_value_map(data.get(future_id) or [])
    smap = to_value_map(data.get(spot_id) or [])
    dates = sorted(set(fmap.keys()) & set(smap.keys()))
    if len(dates) < window + 1:
        return {"future": future_id, "spot": spot_id, "status": "insufficient_data"}
    spreads = [fmap[d] - smap[d] for d in dates]
    recent = spreads[-window:]
    prior = spreads[-2 * window : -window]
    if len(prior) < window:
        return {
            "future": future_id,
            "spot": spot_id,
            "status": "ok",
            "last_spread": spreads[-1],
            "spread_change_vs_prior": None,
        }
    return {
        "future": future_id,
        "spot": spot_id,
        "status": "ok",
        "last_spread": spreads[-1],
        "avg_spread_recent": sum(recent) / len(recent),
        "avg_spread_prior": sum(prior) / len(prior),
        "spread_change_vs_prior": (sum(recent) / len(recent)) - (sum(prior) / len(prior)),
    }

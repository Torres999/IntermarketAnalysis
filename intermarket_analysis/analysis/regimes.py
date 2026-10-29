from __future__ import annotations

from datetime import date

from intermarket_analysis.analysis.normalize import (
    align_dates,
    direction_label,
    pct_returns,
    rolling_sum,
    to_value_map,
)


def assess_four_leg_sync(
    data: dict[str, list[dict[str, object]]],
    *,
    equity_id: str = "csi300",
    bond_yield_id: str = "cn10y_yield",
    fx_id: str = "rmb_cfets",
    commodity_id: str = "nh_commodity",
    window: int = 20,
) -> dict[str, object]:
    maps = {
        "equity": to_value_map(data.get(equity_id) or []),
        "bond_yield": to_value_map(data.get(bond_yield_id) or []),
        "fx": to_value_map(data.get(fx_id) or []),
        "commodity": to_value_map(data.get(commodity_id) or []),
    }
    dates = align_dates(maps)
    if len(dates) < window + 2:
        return {"regime": "unknown", "reason": "insufficient_data", "legs": {}}

    rets = {k: pct_returns(v, dates) for k, v in maps.items()}
    windows = {k: rolling_sum(v, window) for k, v in rets.items()}
    dirs = {k: direction_label(w) for k, w in windows.items()}

    legs = {
        key: {
            "series": sid,
            "window_return": windows[key],
            "direction": dirs[key],
        }
        for key, sid in (
            ("equity", equity_id),
            ("bond_yield", bond_yield_id),
            ("fx", fx_id),
            ("commodity", commodity_id),
        )
    }

    up_count = sum(1 for d in dirs.values() if d == "up")
    down_count = sum(1 for d in dirs.values() if d == "down")
    unknowns = sum(1 for d in dirs.values() if d == "unknown")

    if unknowns >= 2:
        regime = "unknown"
    elif up_count >= 3:
        regime = "aligned_risk_on"
    elif down_count >= 3:
        regime = "aligned_risk_off"
    else:
        regime = "decoupled"

    return {
        "regime": regime,
        "as_of": dates[-1].isoformat(),
        "window_days": window,
        "legs": legs,
        "note": "A-share 股债汇 commodity 20d direction; decoupled ≈ 非黑白市场.",
    }


def assess_three_leg_sync(
    data: dict[str, list[dict[str, object]]],
    **kwargs: object,
) -> dict[str, object]:
    """Backward-compatible wrapper (equity + bond + fx only)."""
    four = assess_four_leg_sync(data, **kwargs)  # type: ignore[arg-type]
    legs = dict(four.get("legs") or {})
    legs.pop("commodity", None)
    return {**four, "legs": legs}

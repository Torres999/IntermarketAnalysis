from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "market.db"
WEB_DIR = ROOT / "web"
BROWSERS_DIR = ROOT / ".browsers"


def bootstrap_env() -> None:
    """Ensure Playwright browser path defaults to the project folder."""
    import os

    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSERS_DIR))

DEFAULT_LOOKBACK_YEARS = 5

AssetClass = Literal[
    "equity_spot",
    "equity_future",
    "bond_yield",
    "bond_price",
    "fx_index",
    "commodity",
    "commodity_index",
]
ScraperKind = Literal[
    "investing_chart",
    "eastmoney_index",
    "chinamoney",
    "chinamoney_yield",
    "cn10y",
    "sina_futures",
    "composite",
]


@dataclass(frozen=True)
class SeriesSpec:
    series_id: str
    name: str
    source_url: str
    unit: str = ""
    asset_class: AssetClass = "equity_spot"
    compare_group: str = ""
    spot_series_id: str | None = None
    default_pair_id: str = ""
    range_label: str = "5年"
    sbcharts_max_value: float | None = None
    sbcharts_min_value: float | None = None
    pd_max_value: float | None = None
    pd_min_value: float | None = None
    quote_tab: str | None = None
    sina_symbol: str | None = None
    scraper: ScraperKind = "investing_chart"
    enabled: bool = True


def _chart(path: str) -> str:
    return f"https://cn.investing.com/{path}"


def _idx(slug: str) -> str:
    """Instrument page with embedded chart (avoid deprecated *-chart URLs that 404)."""
    return _chart(f"indices/{slug}")


def _bond(slug: str) -> str:
    return _chart(f"rates-bonds/{slug}")


SERIES: dict[str, SeriesSpec] = {
    # --- Bonds ---
    "cn10y": SeriesSpec(
        series_id="cn10y",
        name="中国10年期国债价格 (期货/TV)",
        source_url="https://cn.tradingview.com/symbols/TVC-CN10Y/",
        asset_class="bond_price",
        compare_group="bond",
        scraper="cn10y",
    ),
    "cn10y_yield": SeriesSpec(
        series_id="cn10y_yield",
        name="中国10年期国债收益率",
        source_url="https://www.chinamoney.com.cn/chinese/bkcurvclosedyhis/?bondType=CYCC000",
        unit="%",
        asset_class="bond_yield",
        compare_group="bond",
        scraper="chinamoney_yield",
    ),
    # --- FX indices ---
    "rmb_cfets": SeriesSpec(
        series_id="rmb_cfets",
        name="CFETS 人民币汇率指数",
        source_url="https://www.chinamoney.com.cn/chinese/bkrmbidx/",
        unit="点",
        asset_class="fx_index",
        compare_group="rmb",
        scraper="chinamoney",
    ),
    "rmb_bis": SeriesSpec(
        series_id="rmb_bis",
        name="BIS 货币篮子人民币汇率指数",
        source_url="https://www.chinamoney.com.cn/chinese/bkrmbidx/",
        unit="点",
        asset_class="fx_index",
        compare_group="rmb",
        scraper="chinamoney",
    ),
    "rmb_sdr": SeriesSpec(
        series_id="rmb_sdr",
        name="SDR 货币篮子人民币汇率指数",
        source_url="https://www.chinamoney.com.cn/chinese/bkrmbidx/",
        unit="点",
        asset_class="fx_index",
        compare_group="rmb",
        scraper="chinamoney",
    ),
    # --- A-share spot indices ---
    "sse_composite": SeriesSpec(
        series_id="sse_composite",
        name="上证指数",
        source_url="https://quote.eastmoney.com/zs000001.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_broad",
        scraper="eastmoney_index",
    ),
    "sse50": SeriesSpec(
        series_id="sse50",
        name="上证50",
        source_url="https://quote.eastmoney.com/zs000016.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_style",
        scraper="eastmoney_index",
    ),
    "csi300": SeriesSpec(
        series_id="csi300",
        name="沪深300",
        source_url="https://quote.eastmoney.com/zs000300.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_broad",
        scraper="eastmoney_index",
    ),
    "csi500": SeriesSpec(
        series_id="csi500",
        name="中证500",
        source_url="https://quote.eastmoney.com/zs000905.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_style",
        scraper="eastmoney_index",
    ),
    "csi1000": SeriesSpec(
        series_id="csi1000",
        name="中证1000",
        source_url="https://quote.eastmoney.com/zs000852.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_style",
        scraper="eastmoney_index",
    ),
    "szse_component": SeriesSpec(
        series_id="szse_component",
        name="深证成指",
        source_url="https://quote.eastmoney.com/zs399001.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_broad",
        scraper="eastmoney_index",
    ),
    "chinext": SeriesSpec(
        series_id="chinext",
        name="创业板指",
        source_url="https://quote.eastmoney.com/zs399006.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_broad",
        scraper="eastmoney_index",
    ),
    "star50": SeriesSpec(
        series_id="star50",
        name="科创50",
        source_url="https://quote.eastmoney.com/zs000688.html",
        unit="点",
        asset_class="equity_spot",
        compare_group="a_share_style",
        scraper="eastmoney_index",
    ),
    # --- A-share index futures (Sina continuous main) ---
    "future_ih": SeriesSpec(
        series_id="future_ih",
        name="上证50股指期货",
        source_url="https://finance.sina.com.cn/futures/quotes/IH0.shtml",
        unit="点",
        asset_class="equity_future",
        compare_group="future_ih_pair",
        spot_series_id="sse50",
        sina_symbol="IH0",
        scraper="sina_futures",
    ),
    "future_if": SeriesSpec(
        series_id="future_if",
        name="沪深300股指期货",
        source_url="https://finance.sina.com.cn/futures/quotes/IF0.shtml",
        unit="点",
        asset_class="equity_future",
        compare_group="future_if_pair",
        spot_series_id="csi300",
        sina_symbol="IF0",
        scraper="sina_futures",
    ),
    "future_ic": SeriesSpec(
        series_id="future_ic",
        name="中证500股指期货",
        source_url="https://finance.sina.com.cn/futures/quotes/IC0.shtml",
        unit="点",
        asset_class="equity_future",
        compare_group="future_ic_pair",
        spot_series_id="csi500",
        sina_symbol="IC0",
        scraper="sina_futures",
    ),
    "future_im": SeriesSpec(
        series_id="future_im",
        name="中证1000股指期货",
        source_url="https://finance.sina.com.cn/futures/quotes/IM0.shtml",
        unit="点",
        asset_class="equity_future",
        compare_group="future_im_pair",
        spot_series_id="csi1000",
        sina_symbol="IM0",
        scraper="sina_futures",
    ),
    # --- Commodities (Sina continuous futures, HTTP) ---
    "comm_au": SeriesSpec(
        series_id="comm_au",
        name="沪金主连",
        source_url="https://finance.sina.com.cn/futures/quotes/AU0.shtml",
        unit="元/克",
        asset_class="commodity",
        compare_group="commodity",
        sina_symbol="AU0",
        scraper="sina_futures",
    ),
    "comm_cu": SeriesSpec(
        series_id="comm_cu",
        name="沪铜主连",
        source_url="https://finance.sina.com.cn/futures/quotes/CU0.shtml",
        unit="元/吨",
        asset_class="commodity",
        compare_group="commodity",
        sina_symbol="CU0",
        scraper="sina_futures",
    ),
    "comm_sc": SeriesSpec(
        series_id="comm_sc",
        name="原油主连",
        source_url="https://finance.sina.com.cn/futures/quotes/SC0.shtml",
        unit="元/桶",
        asset_class="commodity",
        compare_group="commodity",
        sina_symbol="SC0",
        scraper="sina_futures",
    ),
    "comm_rb": SeriesSpec(
        series_id="comm_rb",
        name="螺纹钢主连",
        source_url="https://finance.sina.com.cn/futures/quotes/RB0.shtml",
        unit="元/吨",
        asset_class="commodity",
        compare_group="commodity",
        sina_symbol="RB0",
        scraper="sina_futures",
    ),
    "nh_commodity": SeriesSpec(
        series_id="nh_commodity",
        name="大宗综合指数（金/铜/油/螺等权）",
        source_url="https://finance.sina.com.cn/futuremarket/",
        unit="点",
        asset_class="commodity_index",
        compare_group="commodity",
        scraper="composite",
    ),
}


def default_start(today: date | None = None) -> date:
    today = today or date.today()
    return today - timedelta(days=365 * DEFAULT_LOOKBACK_YEARS)


def get_series(series_id: str) -> SeriesSpec:
    try:
        return SERIES[series_id]
    except KeyError as exc:
        raise KeyError(f"Unknown series_id: {series_id}") from exc


def enabled_series() -> list[SeriesSpec]:
    return [s for s in SERIES.values() if s.enabled]


def investing_chart_series() -> list[SeriesSpec]:
    return [s for s in enabled_series() if s.scraper == "investing_chart"]


def eastmoney_index_series() -> list[SeriesSpec]:
    return [s for s in enabled_series() if s.scraper == "eastmoney_index"]


def sina_futures_series() -> list[SeriesSpec]:
    return [s for s in enabled_series() if s.scraper == "sina_futures"]


def chart_backfill_series_ids() -> list[str]:
    """Series re-fetched by backfill-charts (5Y button flow)."""
    ids: list[str] = []
    for spec in enabled_series():
        if spec.scraper in ("investing_chart", "eastmoney_index", "cn10y", "chinamoney_yield", "sina_futures"):
            ids.append(spec.series_id)
    return ids

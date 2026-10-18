from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "market.db"
WEB_DIR = ROOT / "web"

DEFAULT_LOOKBACK_YEARS = 5


@dataclass(frozen=True)
class SeriesSpec:
    series_id: str
    name: str
    source_url: str
    unit: str = ""


SERIES = {
    "cn10y": SeriesSpec(
        series_id="cn10y",
        name="中国10年期国债价格 (TV 价格 / 期货)",
        source_url="https://cn.tradingview.com/symbols/TVC-CN10Y/",
        unit="",
    ),
    "cn10y_yield": SeriesSpec(
        series_id="cn10y_yield",
        name="中国10年期国债收益率 (历史保留)",
        source_url="https://cn.investing.com/rates-bonds/china-10-year-bond-yield",
        unit="%",
    ),
    "rmb_cfets": SeriesSpec(
        series_id="rmb_cfets",
        name="CFETS 人民币汇率指数",
        source_url="https://www.chinamoney.com.cn/chinese/bkrmbidx/",
        unit="点",
    ),
    "rmb_bis": SeriesSpec(
        series_id="rmb_bis",
        name="BIS 货币篮子人民币汇率指数",
        source_url="https://www.chinamoney.com.cn/chinese/bkrmbidx/",
        unit="点",
    ),
    "rmb_sdr": SeriesSpec(
        series_id="rmb_sdr",
        name="SDR 货币篮子人民币汇率指数",
        source_url="https://www.chinamoney.com.cn/chinese/bkrmbidx/",
        unit="点",
    ),
    "sse_composite": SeriesSpec(
        series_id="sse_composite",
        name="上证指数",
        source_url="https://cn.investing.com/indices/shanghai-composite",
        unit="点",
    ),
}


def default_start(today: date | None = None) -> date:
    today = today or date.today()
    return today - timedelta(days=365 * DEFAULT_LOOKBACK_YEARS)

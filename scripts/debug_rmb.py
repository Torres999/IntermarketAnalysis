import time
from datetime import date

from scrapling.fetchers import StealthyFetcher

from intermarket_analysis.browser_config import stealth_kwargs
from intermarket_analysis.scrapers.utils import browser_fetch_excel_post
from intermarket_analysis.xlsx_minimal import read_first_sheet_rows

page_url = "https://www.chinamoney.com.cn/chinese/bkrmbidx/"


def try_range(start: date, end: date) -> None:
    t = int(time.time() * 1000)
    excel_url = (
        "https://www.chinamoney.com.cn/dqs/rest/cm-u-bk-fx/RmbIdxHisExcel"
        f"?lang=CN&startDate={start}&endDate={end}&t={t}"
    )
    content = browser_fetch_excel_post(page_url, excel_url)
    rows = read_first_sheet_rows(content)
    print(start, end, "bytes", len(content), "rows", len(rows), "tail", rows[-3:] if rows else None)


if __name__ == "__main__":
    try_range(date(2024, 1, 1), date(2024, 12, 31))
    try_range(date(2025, 1, 1), date(2025, 10, 18))
    try_range(date(2021, 1, 1), date(2021, 12, 31))

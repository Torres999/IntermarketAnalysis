import sqlite3
from datetime import date
from pathlib import Path

from intermarket_analysis.config import default_start
from intermarket_analysis.scrapers.cn10y import fetch_cn10y
from intermarket_analysis.storage import clear_series_data, init_db, upsert_observations

init_db()
clear_series_data(["cn10y"])
points = fetch_cn10y(default_start(), date.today())
print("upsert", upsert_observations("cn10y", points))

db = Path(__file__).resolve().parents[1] / "data" / "market.db"
con = sqlite3.connect(db)
print("cn10y_yield rows", con.execute("SELECT COUNT(*) FROM observations WHERE series_id='cn10y_yield'").fetchone()[0])
print(
    "cn10y",
    con.execute(
        "SELECT COUNT(*), MIN(obs_date), MAX(obs_date), MIN(value), MAX(value) "
        "FROM observations WHERE series_id='cn10y'"
    ).fetchone(),
)

"""Step 1 of the Contract Value project: download last season's advanced
player stats from Basketball Reference and save them to SQLite."""

import sqlite3
import urllib.request
from io import StringIO

import pandas as pd

SEASON_END_YEAR = 2026  # the 2025-26 season
URL = f"https://www.basketball-reference.com/leagues/NBA_{SEASON_END_YEAR}_advanced.html"
DB_PATH = "nba_contracts.db"
TEXT_COLUMNS = ["Player", "Team", "Tm", "Pos", "Awards"]


def fetch_advanced(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        html = response.read().decode("utf-8")
    return pd.read_html(StringIO(html))[0]


def clean(df):
    # The table repeats its header row every 20 players and ends with a league average row.
    df = df[df["Player"].notna() & ~df["Player"].isin(["Player", "League Average"])]
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")].copy()
    # Traded players get one row per team plus a combined row (2TM, 3TM) listed first.
    # ponytail: dedupes on name, so two players with the same name would collide.
    df = df.drop_duplicates(subset="Player", keep="first")
    for col in df.columns:
        if col not in TEXT_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def save(df, db_path):
    with sqlite3.connect(db_path) as conn:
        df.to_sql("advanced", conn, if_exists="replace", index=False)


if __name__ == "__main__":
    stats = clean(fetch_advanced(URL))
    save(stats, DB_PATH)
    print(f"Saved {len(stats):,} players to the advanced table in {DB_PATH}\n")
    print("Top 10 by VORP:")
    print(stats.nlargest(10, "VORP")[["Player", "Team", "G", "MP", "WS", "BPM", "VORP"]].to_string(index=False))
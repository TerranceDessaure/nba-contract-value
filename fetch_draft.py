"""Step 2b of the Contract Value project: list every player still on a
rookie-scale contract, so we can set those automatic bargains aside.

Rookie-scale deals cover a first-round pick's first 4 seasons, so in 2026-27
that's every first-round pick from the 2023 through 2026 drafts."""

import sqlite3
import time

import pandas as pd

from fetch_advanced import DB_PATH, fetch_advanced as fetch_table

DRAFT_YEARS = range(2023, 2027)
URL = "https://www.basketball-reference.com/draft/NBA_{year}.html"


def first_round(df, year):
    # The draft table has a two-row header; keep the bottom row.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)
    picks = pd.to_numeric(df["Pk"], errors="coerce")  # header and "Round 2" rows become NaN
    # ponytail: assumes picks 1-30 are the first round; a forfeited pick would shift this by one.
    df = df[picks <= 30]
    return pd.DataFrame({"Player": df["Player"], "draft_year": year, "pick": picks[picks <= 30].astype(int)})


if __name__ == "__main__":
    frames = []
    for year in DRAFT_YEARS:
        frames.append(first_round(fetch_table(URL.format(year=year)), year))
        print(f"{year} draft: {len(frames[-1])} first-round picks")
        time.sleep(3)  # Basketball Reference blocks scripts that request pages too fast

    rookies = pd.concat(frames, ignore_index=True)
    with sqlite3.connect(DB_PATH) as conn:
        rookies.to_sql("rookie_scale", conn, if_exists="replace", index=False)
    print(f"\nSaved {len(rookies)} rookie-scale players to the rookie_scale table in {DB_PATH}")
"""Step 2 of the Contract Value project: download current NBA contracts from
Basketball Reference and save each player's salary and current team."""

import sqlite3

import pandas as pd

from fetch_advanced import DB_PATH, fetch_advanced as fetch_table

URL = "https://www.basketball-reference.com/contracts/players.html"
SALARY_SEASON = "2026-27"


def clean(df):
    # The table has a two-row header ("Salary" above the season columns); keep the bottom row.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)
    team_col = "Team" if "Team" in df.columns else "Tm"
    df = df[df["Player"].notna() & (df["Player"] != "Player")].copy()
    df["salary"] = pd.to_numeric(
        df[SALARY_SEASON].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"
    )
    df = df.dropna(subset=["salary"])
    # A waived player can be on two teams' books. Keep his biggest (active) contract.
    # ponytail: dead money owed by an old team is dropped, not added to the total.
    df = df.sort_values("salary", ascending=False).drop_duplicates(subset="Player")
    return df[["Player", team_col, "salary"]].rename(columns={team_col: "current_team"})


def save(df, db_path):
    with sqlite3.connect(db_path) as conn:
        df.to_sql("salaries", conn, if_exists="replace", index=False)


if __name__ == "__main__":
    salaries = clean(fetch_table(URL))
    save(salaries, DB_PATH)
    print(f"Saved {len(salaries):,} {SALARY_SEASON} contracts to the salaries table in {DB_PATH}\n")
    print("Highest paid:")
    print(salaries.head(10).to_string(index=False, formatters={"salary": "${:,.0f}".format}))
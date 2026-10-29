"""Step 3 of the Contract Value project: compare each player's 2026-27 salary
to what his 2025-26 production is worth on the open market, and find the
biggest bargains and overpays."""

import sqlite3

import numpy as np
import pandas as pd

DB_PATH = "nba_contracts.db"
MIN_MINUTES = 500  # skip players who barely played; their stats are noise

QUERY = """
SELECT a.Player, s.current_team, a.Pos, a.Age, a.G, a.MP, a.WS, a.BPM, a.VORP, s.salary,
    r.Player IS NOT NULL AS rookie_deal
FROM advanced AS a
JOIN salaries AS s ON a.Player = s.Player
LEFT JOIN rookie_scale AS r ON a.Player = r.Player
WHERE a.MP >= ?
"""

# Rookies whose draft-page name doesn't match the stats page would silently
# be treated as veterans. 2026 picks are skipped: they haven't played yet.
UNMATCHED_ROOKIES = """
SELECT Player, draft_year FROM rookie_scale
WHERE draft_year < 2026 AND Player NOT IN (SELECT Player FROM advanced)
"""

UNMATCHED = """
SELECT COUNT(*) FROM salaries
WHERE Player NOT IN (SELECT Player FROM advanced)
"""


def money(x):
    return f"${x / 1e6:,.1f}M"


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        players = pd.read_sql(QUERY, conn, params=(MIN_MINUTES,))
        unmatched = conn.execute(UNMATCHED).fetchone()[0]
        unmatched_rookies = pd.read_sql(UNMATCHED_ROOKIES, conn)

        # The league's going rate: a straight line through salary vs. VORP for
        # negotiated contracts only. Rookie-scale pay is set by rule, so it would drag the line down.
        veterans = players[players["rookie_deal"] == 0]
        slope, intercept = np.polyfit(veterans["VORP"], veterans["salary"], 1)
        # No one can be paid more than the max or less than the minimum, so the
        # model can't say a player is "worth" more or less than that either.
        players["expected_salary"] = (intercept + slope * players["VORP"]).clip(
            lower=veterans["salary"].min(), upper=veterans["salary"].max()
        )
        players["value_gap"] = players["expected_salary"] - players["salary"]
        players = players.sort_values("value_gap", ascending=False)
        players.to_sql("contract_value", conn, if_exists="replace", index=False)

    print(f"Matched {len(players):,} players with {MIN_MINUTES}+ minutes to a contract")
    print(f"{unmatched:,} contracts had no stats last season (rookies, injured, or name mismatch)")
    print(f"{players['rookie_deal'].sum():,} rookie-scale deals set aside (still saved, flagged rookie_deal = 1)")
    if len(unmatched_rookies):
        print(f"Check these {len(unmatched_rookies)} drafted players with no stats (didn't play, or a name mismatch?):")
        print("  " + ", ".join(unmatched_rookies["Player"]))
    print(f"Going rate: each point of VORP is worth about {money(slope)} per year\n")

    negotiated = players[players["rookie_deal"] == 0]
    cols = ["Player", "current_team", "VORP", "salary", "expected_salary", "value_gap"]
    fmt = {c: money for c in ["salary", "expected_salary", "value_gap"]}
    fmt["VORP"] = "{:.1f}".format
    print("Biggest bargains (negotiated contracts):")
    print(negotiated.head(10)[cols].to_string(index=False, formatters=fmt))
    print("\nBiggest overpays (negotiated contracts):")
    print(negotiated.tail(10)[cols].iloc[::-1].to_string(index=False, formatters=fmt))
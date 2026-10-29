# NBA Contract Value: Who's a Bargain and Who's Overpaid?

**Live app:** [ADD YOUR STREAMLIT LINK HERE]

Every NBA front office asks the same question under the salary cap: how much production are we getting for each dollar? This project compares every player's **2026-27 salary** to what his **2025-26 production** is worth at the league's going rate, then ranks the biggest bargains and the worst contracts.

## What the dashboard does

- **Salary vs. production scatter plot.** The gray line is the league's going rate. Players below it are bargains; players above it are overpaid. Hover over any dot to see salary, estimated worth, and the gap.
- **Team filter** to review one team's books.
- **Rookie toggle** to show or hide rookie-scale contracts (hidden by default, see below).
- **Best bargains** and **Worst contracts** tables.

## How it works

| Step | Script | What it does |
|---|---|---|
| Collect production | `fetch_advanced.py` | Downloads 2025-26 advanced stats (VORP, Win Shares, BPM) from Basketball Reference |
| Collect salaries | `fetch_salaries.py` | Downloads 2026-27 contracts and each player's current team |
| Collect draft data | `fetch_draft.py` | Lists first-round picks from the 2023-2026 drafts, who are on rookie-scale deals |
| Model | `contract_value.py` | SQL joins + a regression line of salary vs. VORP: the league's going rate |
| Deliver | `app.py` | Interactive Streamlit dashboard |

**Production** is measured with **VORP** (Value Over Replacement Player): value added over a minimum-salary, replacement-level player. Zero VORP is what a minimum contract buys, so the line's slope is the price of production above the cheapest option.

**Value gap** = expected salary − actual salary. Positive = bargain. Negative = overpaid.

## Modeling decisions

- **Rookie-scale contracts are set aside.** Rookie pay is fixed by league rules, so young stars are automatic "bargains" that no GM can act on. They're left out of the going-rate line and the rankings (the dashboard can still show them).
- **Expected salary is capped at the league's real minimum and maximum.** Without this, the model said Shai Gilgeous-Alexander was "worth" $64.8M, more than any player is allowed to earn, and gave negative salaries to below-replacement players.
- **Players with fewer than 500 minutes are excluded** because their stats are too noisy.
- **Traded players** use their combined season totals, counted once, and are assigned to their current team.

## Data validation

- A check lists any drafted player who has no match on the stats page, to catch silent name mismatches. The two flagged players (Jalen Hood-Schifino and Thomas Sorber) did not play last season, so name matching is clean.
- LeBron James at $3.9M looked like an error. It's real: he signed a two-year, roughly $8M deal with the 76ers.

## Key findings

- **The going rate is about $7.0M per point of VORP per year.**
- **Top negotiated bargains:** Payton Pritchard, Neemias Queta, Deni Avdija, and LeBron James. Two of the top bargains play for Boston.
- **Worst contracts:** [FILL IN FROM THE DASHBOARD]
- **Injuries drive many "overpaid" labels.** VORP is a counting stat, so stars who missed much of last season look overpaid. Availability has real value, but a one-time injury can make a fair contract look bad.

## Limitations

- VORP is built from box scores and underrates defense that doesn't show up as steals or blocks.
- One season of production. A multi-season average would be more stable.
- A player waived by one team and signed by another is assigned to his larger contract, which may not be his current team.
- Picks 1-30 are treated as the first round; a forfeited pick would shift this by one.
- A straight line is a simple model of the market; real contracts also depend on age, cap space, and timing.

## Run it yourself

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python fetch_advanced.py
python fetch_salaries.py
python fetch_draft.py
python contract_value.py
streamlit run app.py
```

## Built with

Python, pandas, NumPy, SQLite, SQL, Altair, Streamlit

*By Terrance Dessaure, Information Science and Technology, University of South Carolina Beaufort*
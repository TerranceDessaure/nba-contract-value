"""Step 4 of the Contract Value project: the dashboard a front office can use.
Run it with:  streamlit run app.py"""

import sqlite3

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

DB_PATH = "nba_contracts.db"


@st.cache_data
def load():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM contract_value", conn)
    return df.assign(
        label=np.where(df["value_gap"] >= 0, "Bargain", "Overpaid"),
        salary_m=df["salary"] / 1e6,
        worth_m=df["expected_salary"] / 1e6,
        gap_m=df["value_gap"] / 1e6,
        value_per_dollar=df["expected_salary"] / df["salary"],
    )


def money(m):
    return f"{'-' if m < 0 else ''}${abs(m):,.1f}M"


df = load()
veterans = df[df["rookie_deal"] == 0]
# Same fit as contract_value.py (same players), so this is the model's going rate.
going_rate = np.polyfit(veterans["VORP"], veterans["salary_m"], 1)[0]

st.title("NBA Contract Value, 2026-27")
st.markdown(
    "**Which NBA contracts give teams the most production per dollar?** "
    "Each player's 2026-27 salary is compared with what his 2025-26 production "
    "is worth at the league's going rate."
)

best, worst = veterans.nlargest(1, "value_gap").iloc[0], veterans.nsmallest(1, "value_gap").iloc[0]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Players analyzed", f"{len(veterans):,}", help="Negotiated contracts, 500+ minutes last season.")
k2.metric("Going rate", f"{money(going_rate)} / VORP", help="What teams pay, per year, for each point of VORP.")
k3.metric("Best bargain", best["Player"], f"+{money(best['gap_m'])}")
k4.metric("Worst contract", worst["Player"], money(worst["gap_m"]), delta_color="normal")

with st.expander("How to read this dashboard"):
    st.markdown(
        """
- **VORP (Value Over Replacement Player):** value a player added last season compared
  to a minimum-salary replacement. 0 = replacement level, 4+ ≈ All-Star, 7+ ≈ MVP level.
  It's a *counting* stat, so players who missed games score lower.
- **Each dot is a player.** Further right = more production. Higher = bigger salary.
- **The gray line is the going rate:** what a typical team pays for that much production.
  - **Below the line (teal) = bargain:** paid less than his production is worth.
  - **Above the line (orange) = overpaid:** paid more than his production is worth.
- **Value gap** = worth − salary. **Value per dollar** = worth ÷ salary (2.0x means he
  produces like a player paid twice as much).
- **Rookie-scale contracts are hidden by default:** rookie pay is set by league rules, so
  those players are automatic bargains no GM can act on.
"""
    )

st.subheader("Explore")
f1, f2 = st.columns([2, 1])
team = f1.selectbox("Team", ["All teams"] + sorted(df["current_team"].unique()))
show_rookies = f2.checkbox("Include rookie-scale contracts")

view = df if show_rookies else veterans
if team != "All teams":
    view = view[view["current_team"] == team]
    t1, t2, t3 = st.columns(3)
    t1.metric(f"{team} payroll shown", money(view["salary_m"].sum()))
    t2.metric("Production worth", money(view["worth_m"].sum()))
    t3.metric("Net value", money(view["gap_m"].sum()),
              help="Positive = the team gets more production than it pays for.")

line = alt.Chart(veterans).mark_line(color="gray").encode(x="VORP:Q", y="worth_m:Q")
dots = alt.Chart(view).mark_circle(size=70, opacity=0.8).encode(
    x=alt.X("VORP:Q", title="Production last season (VORP)"),
    y=alt.Y("salary_m:Q", title="2026-27 salary ($ millions)"),
    color=alt.Color(
        "label:N",
        scale=alt.Scale(domain=["Bargain", "Overpaid"], range=["#2a9d8f", "#e76f51"]),
        title=None,
    ),
    tooltip=[
        "Player",
        alt.Tooltip("current_team", title="Team"),
        alt.Tooltip("VORP", format=".1f"),
        alt.Tooltip("salary_m", title="Salary ($M)", format=".1f"),
        alt.Tooltip("worth_m", title="Worth ($M)", format=".1f"),
        alt.Tooltip("gap_m", title="Value gap ($M)", format="+.1f"),
        alt.Tooltip("value_per_dollar", title="Value per dollar", format=".1f"),
    ],
)
st.altair_chart(line + dots, use_container_width=True)

columns = {
    "Player": "Player",
    "current_team": "Team",
    "VORP": "VORP",
    "salary_m": "Salary ($M)",
    "worth_m": "Worth ($M)",
    "gap_m": "Gap ($M)",
    "value_per_dollar": "Value per $",
}
table = view[list(columns)].rename(columns=columns).round(1)

left, right = st.columns(2)
left.subheader("Best bargains")
left.dataframe(table.nlargest(10, "Gap ($M)"), hide_index=True)
right.subheader("Worst contracts")
right.dataframe(table.nsmallest(10, "Gap ($M)"), hide_index=True)

st.subheader("Look up a player")
name = st.selectbox("Player", sorted(view["Player"]), index=None, placeholder="Type a name")
if name:
    p = view[view["Player"] == name].iloc[0]
    verdict = "a bargain" if p["gap_m"] >= 0 else "overpaid"
    st.markdown(
        f"**{name}** ({p['current_team']}) earns **{money(p['salary_m'])}** in 2026-27. "
        f"His {p['VORP']:.1f} VORP last season is worth about **{money(p['worth_m'])}** at the "
        f"going rate, so he's **{verdict}** by {money(abs(p['gap_m']))} "
        f"({p['value_per_dollar']:.1f}x value per dollar)."
        + (" *Rookie-scale contract: pay is set by league rules.*" if p["rookie_deal"] else "")
    )

st.caption(
    "Data: Basketball Reference (2025-26 advanced stats, 2026-27 contracts, 2023-2026 drafts). "
    "Expected salary is capped between the league's minimum and maximum salaries. "
    "VORP underrates defense that doesn't show up in the box score."
)
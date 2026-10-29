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
    )


st.title("NBA Contract Value, 2026-27")
st.caption(
    "Each player's 2026-27 salary vs. what his 2025-26 production (VORP) is worth "
    "at the league's going rate. Below the gray line = bargain. Above it = overpaid."
)

df = load()
team = st.selectbox("Team", ["All teams"] + sorted(df["current_team"].unique()))
show_rookies = st.checkbox(
    "Include rookie-scale contracts",
    help="Rookie pay is set by league rules, so these players are bargains automatically.",
)

view = df if show_rookies else df[df["rookie_deal"] == 0]
if team != "All teams":
    view = view[view["current_team"] == team]

going_rate = alt.Chart(df[df["rookie_deal"] == 0]).mark_line(color="gray").encode(
    x="VORP:Q", y="worth_m:Q"
)
players = alt.Chart(view).mark_circle(size=70, opacity=0.8).encode(
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
        alt.Tooltip("salary_m", title="Salary ($M)", format=".1f"),
        alt.Tooltip("worth_m", title="Worth ($M)", format=".1f"),
        alt.Tooltip("gap_m", title="Value gap ($M)", format="+.1f"),
    ],
)
st.altair_chart(going_rate + players, use_container_width=True)

columns = {
    "Player": "Player",
    "current_team": "Team",
    "VORP": "VORP",
    "salary_m": "Salary ($M)",
    "worth_m": "Worth ($M)",
    "gap_m": "Gap ($M)",
}
table = view[list(columns)].rename(columns=columns).round(1)

left, right = st.columns(2)
left.subheader("Best bargains")
left.dataframe(table.nlargest(10, "Gap ($M)"), hide_index=True)
right.subheader("Worst contracts")
right.dataframe(table.nsmallest(10, "Gap ($M)"), hide_index=True)
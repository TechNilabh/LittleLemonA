"""
CP Insight — Streamlit Standalone Dashboard
Calls the Codeforces API directly via cf_client (no Django server required).

Run: streamlit run streamlit_app.py
"""
import sys
import os
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------------------
# Allow importing cf_client without Django's manage.py machinery.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))
from cpinsight.cf_client import get_user_info, get_user_rating, get_user_submissions  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CP Insight — Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal dark-themed CSS
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background-color: #0f1117; color: #f8fafc; }
  [data-testid="stSidebar"] { background-color: #161922; border-right: 2px solid #262a36; }
  .stat-box { background: #161922; border: 2px solid #262a36; padding: 1rem 1.2rem; margin-bottom: .75rem; }
  .stat-label { font-size: .75rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: .06em; }
  .stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 800; color: #7c3aed; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("⚡ CP INSIGHT")
st.sidebar.markdown("Codeforces Analytics Dashboard")
handle = st.sidebar.text_input("Codeforces Handle", placeholder="e.g. tourist")
analyze_btn = st.sidebar.button("Analyze", use_container_width=True)

# ---------------------------------------------------------------------------
# Main content — only runs when button is pressed
# ---------------------------------------------------------------------------
if analyze_btn:
    if not handle.strip():
        st.warning("Please enter a Codeforces handle first.")
        st.stop()

    handle = handle.strip()

    with st.spinner(f"Fetching data for **{handle}** …"):
        try:
            profile = get_user_info(handle)
            ratings = get_user_rating(handle)
            submissions = get_user_submissions(handle)
        except Exception as exc:
            st.error(f"⚠️ Could not fetch data for **{handle}**: {exc}")
            st.stop()

    # -----------------------------------------------------------------------
    # Profile header
    # -----------------------------------------------------------------------
    st.title(f"📊 `{profile['handle']}`")

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Current Rating", profile.get("rating", 0)),
        ("Max Rating",     profile.get("maxRating", 0)),
        ("Rank",           (profile.get("rank") or "Unrated").title()),
        ("Contribution",   profile.get("contribution", 0)),
    ]
    for col, (label, value) in zip([col1, col2, col3, col4], metrics):
        col.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-label">{label}</div>'
            f'<div class="stat-value">{value}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # Chart 1: Rating timeline (line)
    # -----------------------------------------------------------------------
    st.subheader("📈 Rating Timeline")
    if ratings:
        df_r = pd.DataFrame(ratings)
        df_r["date"] = pd.to_datetime(df_r["ratingUpdateTimeSeconds"], unit="s")
        fig_line = px.line(
            df_r,
            x="date",
            y="newRating",
            markers=True,
            labels={"newRating": "Rating", "date": "Contest Date"},
        )
        fig_line.update_traces(
            line_color="#7c3aed",
            marker=dict(color="#7c3aed", size=6),
        )
        fig_line.update_layout(
            paper_bgcolor="#161922",
            plot_bgcolor="#0f1117",
            font=dict(color="#94a3b8", family="JetBrains Mono"),
            xaxis=dict(gridcolor="#262a36"),
            yaxis=dict(gridcolor="#262a36"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No contest history found for this handle.")

    # -----------------------------------------------------------------------
    # Chart 2: Verdict breakdown (pie — AC / WA / TLE / Other)
    # -----------------------------------------------------------------------
    st.subheader("🎯 Verdict Breakdown")
    if submissions:
        verdict_map: dict[str, int] = {}
        for sub in submissions:
            raw = sub.get("verdict", "")
            if raw == "OK":
                key = "AC"
            elif raw == "WRONG_ANSWER":
                key = "WA"
            elif raw == "TIME_LIMIT_EXCEEDED":
                key = "TLE"
            else:
                key = "Other"
            verdict_map[key] = verdict_map.get(key, 0) + 1

        df_v = pd.DataFrame(list(verdict_map.items()), columns=["Verdict", "Count"])
        color_map = {"AC": "#47cf73", "WA": "#f44336", "TLE": "#ff9800", "Other": "#94a3b8"}
        fig_pie = px.pie(
            df_v,
            values="Count",
            names="Verdict",
            color="Verdict",
            color_discrete_map=color_map,
            hole=0.35,
        )
        fig_pie.update_layout(
            paper_bgcolor="#161922",
            font=dict(color="#94a3b8", family="JetBrains Mono"),
            legend=dict(orientation="h"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No submission history found for this handle.")

else:
    # Placeholder before the button is pressed
    st.markdown("""
    ## ⚡ CP Insight — Streamlit Analytics
    Enter a **Codeforces handle** in the sidebar and click **Analyze** to load the interactive charts.
    """)

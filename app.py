"""
app.py
Streamlit dashboard for your Codeforces + LeetCode stats.

Run:
    streamlit run app.py

Make sure you've run fetch_data.py first so data/codeforces.json
and data/leetcode.json exist.
"""

import streamlit as st
import pandas as pd

from analyze import (
    load_codeforces,
    load_leetcode,
    cf_rating_history_df,
    cf_solved_by_tag,
    cf_solved_by_difficulty,
    cf_weak_tags,
    lc_solved_by_difficulty,
    lc_top_tags,
)

st.set_page_config(page_title="CP Tracker", layout="wide")
st.title("Competitive Programming Tracker")
st.caption("Codeforces + LeetCode stats in one place")

# ---------- Load data ----------
try:
    cf_data = load_codeforces()
    lc_data = load_leetcode()
except FileNotFoundError:
    st.error(
        "No data found. Run `python fetch_data.py --cf-handle YOUR_HANDLE "
        "--lc-username YOUR_USERNAME` first."
    )
    st.stop()

# ---------- Codeforces section ----------
st.header("Codeforces")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Rating over time")
    rating_df = cf_rating_history_df(cf_data)
    if not rating_df.empty:
        st.line_chart(rating_df.set_index("date")["rating"])
        st.metric("Current rating", int(rating_df["rating"].iloc[-1]))
    else:
        st.info("No rated contests found yet.")

with col2:
    st.subheader("Solved by difficulty bucket")
    diff_df = cf_solved_by_difficulty(cf_data)
    if not diff_df.empty:
        st.bar_chart(diff_df.set_index("difficulty")["solved"])

st.subheader("Solved by tag")
tag_df = cf_solved_by_tag(cf_data)
st.bar_chart(tag_df.set_index("tag")["solved"])

st.subheader("Weak topics (attempted a lot, low solve rate)")
weak_df = cf_weak_tags(cf_data)
st.dataframe(weak_df, use_container_width=True)

st.divider()

# ---------- LeetCode section ----------
st.header("LeetCode")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Solved by difficulty")
    lc_diff_df, total_solved = lc_solved_by_difficulty(lc_data)
    st.metric("Total solved", int(total_solved))
    st.bar_chart(lc_diff_df.set_index("difficulty")["count"])

with col4:
    st.subheader("Top tags")
    lc_tag_df = lc_top_tags(lc_data)
    st.bar_chart(lc_tag_df.set_index("tag")["solved"])

st.caption("Data pulled via Codeforces public API and LeetCode's GraphQL endpoint.")

"""
app.py
Streamlit dashboard for Codeforces + LeetCode stats.

Run:
    streamlit run app.py

Type a Codeforces handle and/or LeetCode username in the sidebar and
click "Fetch stats" - no need to run fetch_data.py separately anymore.
"""

import streamlit as st

from fetch_data import get_codeforces_data, get_leetcode_data
from analyze import (
    cf_rating_history_df,
    cf_solved_by_tag,
    cf_solved_by_difficulty,
    cf_weak_tags,
    lc_solved_by_difficulty,
    lc_top_tags,
)

st.set_page_config(page_title="CP Tracker", layout="wide")
st.title("Competitive Programming Tracker")
st.caption("Enter a Codeforces handle and/or LeetCode username to see stats")

# ---------- Sidebar: user input ----------
with st.sidebar:
    st.header("Lookup")
    cf_handle = st.text_input("Codeforces handle", placeholder="e.g. CipherBug")
    lc_username = st.text_input("LeetCode username", placeholder="e.g. CipherBug")
    fetch_clicked = st.button("Fetch stats", type="primary")

# session_state keeps the fetched data around across reruns,
# so the dashboard doesn't re-fetch every time you interact with a widget
if "cf_data" not in st.session_state:
    st.session_state.cf_data = None
if "lc_data" not in st.session_state:
    st.session_state.lc_data = None

if fetch_clicked:
    if not cf_handle and not lc_username:
        st.sidebar.warning("Enter at least one handle/username.")
    else:
        if cf_handle:
            with st.spinner(f"Fetching Codeforces data for '{cf_handle}'..."):
                try:
                    st.session_state.cf_data = get_codeforces_data(cf_handle)
                except Exception as e:
                    st.session_state.cf_data = None
                    st.sidebar.error(f"Codeforces fetch failed: {e}")

        if lc_username:
            with st.spinner(f"Fetching LeetCode data for '{lc_username}'..."):
                try:
                    st.session_state.lc_data = get_leetcode_data(lc_username)
                except Exception as e:
                    st.session_state.lc_data = None
                    st.sidebar.error(f"LeetCode fetch failed: {e}")

cf_data = st.session_state.cf_data
lc_data = st.session_state.lc_data

if cf_data is None and lc_data is None:
    st.info("Enter a handle/username in the sidebar and click **Fetch stats** to begin.")
    st.stop()

# ---------- Codeforces section ----------
if cf_data:
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
    if not tag_df.empty:
        st.bar_chart(tag_df.set_index("tag")["solved"])

    st.subheader("Weak topics (attempted a lot, low solve rate)")
    weak_df = cf_weak_tags(cf_data)
    st.dataframe(weak_df, use_container_width=True)

    st.divider()

# ---------- LeetCode section ----------
if lc_data:
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

st.caption("Data pulled live via Codeforces public API and LeetCode's GraphQL endpoint.")

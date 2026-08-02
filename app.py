"""
app.py
Streamlit dashboard for Codeforces + LeetCode stats.

Run:
    streamlit run app.py

Type a Codeforces handle and/or LeetCode username in the sidebar and
click "Fetch stats" - no need to run fetch_data.py separately anymore.
"""

import streamlit as st
import plotly.graph_objects as go

from fetch_data import get_codeforces_data, get_leetcode_data, get_leetcode_contest_data
from analyze import (
    cf_rating_history_df,
    cf_solved_by_tag,
    cf_solved_by_difficulty,
    cf_weak_tags,
    lc_solved_by_difficulty,
    lc_top_tags,
    lc_contest_rating_df,
)

st.set_page_config(page_title="CP Tracker", layout="wide", page_icon="🧩")

# ---------- Palette ----------
BG_CARD = "#161B26"
ACCENT_CF = "#7C9EFF"        # blue - Codeforces
ACCENT_LC = "#FFB067"        # amber - LeetCode
ACCENT_CONTEST = "#7CE0C0"   # teal - Contests
TEXT_MUTED = "#9CA3AF"

# ---------- Global CSS ----------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"]  {{
        font-family: 'Inter', sans-serif;
    }}

    .hero-title {{
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, {ACCENT_CF}, {ACCENT_CONTEST});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }}
    .hero-caption {{
        color: {TEXT_MUTED};
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }}

    .section-label {{
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {TEXT_MUTED};
        margin: 1.2rem 0 0.4rem 0;
    }}

    .metric-card {{
        background-color: {BG_CARD};
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        border: 1px solid rgba(255,255,255,0.06);
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: {TEXT_MUTED};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .metric-value {{
        font-size: 1.7rem;
        font-weight: 800;
        margin-top: 0.15rem;
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
    }}

    .empty-state {{
        text-align: center;
        padding: 3rem 1rem;
        color: {TEXT_MUTED};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def metric_card(label: str, value: str, accent: str, col=None):
    """Render a small styled metric card (replacement for st.metric)."""
    target = col if col is not None else st
    target.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{accent}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def styled_line_chart(df, x_col, y_col, color, hover_name=None, y_title=None):
    """A Plotly line chart themed to match the dashboard."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines+markers",
            line=dict(width=3, color=color),
            marker=dict(size=6, color=color),
            text=df[hover_name] if hover_name else None,
            hovertemplate=(
                (f"<b>%{{text}}</b><br>" if hover_name else "")
                + f"{y_title or y_col}: %{{y}}<br>%{{x|%b %d, %Y}}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title=y_title or y_col),
        font=dict(family="Inter, sans-serif", color="#E6E8EC"),
    )
    return fig


def styled_bar_chart(df, x_col, y_col, color, horizontal=False):
    """A Plotly bar chart themed to match the dashboard."""
    fig = go.Figure()
    if horizontal:
        fig.add_trace(go.Bar(y=df[x_col], x=df[y_col], orientation="h", marker=dict(color=color)))
    else:
        fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], marker=dict(color=color)))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        font=dict(family="Inter, sans-serif", color="#E6E8EC"),
    )
    return fig


# ---------- Hero header ----------
st.markdown('<div class="hero-title">Competitive Programming Tracker</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-caption">Live Codeforces + LeetCode stats, contest history, and weak-spot analysis.</div>',
    unsafe_allow_html=True,
)

# ---------- Lookup form (main page, so it's visible on mobile without opening a sidebar) ----------
with st.container():
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("##### 🔍 Lookup")
    col_cf, col_lc = st.columns(2)
    with col_cf:
        cf_handle = st.text_input("Codeforces handle", placeholder="e.g. CipherBug")
    with col_lc:
        lc_username = st.text_input("LeetCode username", placeholder="e.g. CipherBug")
    fetch_clicked = st.button("Fetch stats", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------- Sidebar: kept as a shortcut for desktop users, mirrors the main form ----------
with st.sidebar:
    st.caption("Data pulled live via the Codeforces public API and LeetCode's GraphQL endpoint.")

# session_state keeps the fetched data around across reruns,
# so the dashboard doesn't re-fetch every time you interact with a widget
if "cf_data" not in st.session_state:
    st.session_state.cf_data = None
if "lc_data" not in st.session_state:
    st.session_state.lc_data = None
if "lc_contest_data" not in st.session_state:
    st.session_state.lc_contest_data = None

if fetch_clicked:
    if not cf_handle and not lc_username:
        st.warning("Enter at least one handle/username.")
    else:
        if cf_handle:
            with st.spinner(f"Fetching Codeforces data for '{cf_handle}'..."):
                try:
                    st.session_state.cf_data = get_codeforces_data(cf_handle)
                except Exception as e:
                    st.session_state.cf_data = None
                    st.error(f"Codeforces fetch failed: {e}")

        if lc_username:
            with st.spinner(f"Fetching LeetCode data for '{lc_username}'..."):
                try:
                    st.session_state.lc_data = get_leetcode_data(lc_username)
                except Exception as e:
                    st.session_state.lc_data = None
                    st.error(f"LeetCode fetch failed: {e}")

            with st.spinner(f"Fetching LeetCode contest history for '{lc_username}'..."):
                try:
                    st.session_state.lc_contest_data = get_leetcode_contest_data(lc_username)
                except Exception as e:
                    st.session_state.lc_contest_data = None
                    st.error(f"LeetCode contest fetch failed: {e}")

cf_data = st.session_state.cf_data
lc_data = st.session_state.lc_data
lc_contest_data = st.session_state.lc_contest_data

if cf_data is None and lc_data is None:
    st.markdown(
        """
        <div class="empty-state">
            <div style="font-size:2.5rem;">🧩</div>
            <div style="font-size:1.1rem; font-weight:600; margin-top:0.5rem;">Nothing to show yet</div>
            <div>Enter a handle/username in the sidebar and click <b>Fetch stats</b> to begin.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ---------- Build tabs based on available data ----------
tab_labels = []
if cf_data:
    tab_labels.append("🟦 Codeforces")
if lc_data:
    tab_labels.append("🟧 LeetCode")
if lc_contest_data and lc_contest_data.get("summary"):
    tab_labels.append("🏆 Contests")

tabs = st.tabs(tab_labels)
tab_idx = 0

# ---------- Codeforces tab ----------
if cf_data:
    with tabs[tab_idx]:
        rating_df = cf_rating_history_df(cf_data)

        st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        current_rating = int(rating_df["rating"].iloc[-1]) if not rating_df.empty else "—"
        metric_card("Current Rating", str(current_rating), ACCENT_CF, c1)
        metric_card("Rated Contests", str(len(rating_df)), ACCENT_CF, c2)
        metric_card("Handle", cf_handle or "—", ACCENT_CF, c3)

        st.markdown('<div class="section-label">Rating over time</div>', unsafe_allow_html=True)
        if not rating_df.empty:
            st.plotly_chart(
                styled_line_chart(rating_df, "date", "rating", ACCENT_CF, hover_name="contest", y_title="Rating"),
                use_container_width=True,
            )
        else:
            st.info("No rated contests found yet.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-label">Solved by difficulty</div>', unsafe_allow_html=True)
            diff_df = cf_solved_by_difficulty(cf_data)
            if not diff_df.empty:
                st.plotly_chart(
                    styled_bar_chart(diff_df, "difficulty", "solved", ACCENT_CF),
                    use_container_width=True,
                )
        with col_b:
            st.markdown('<div class="section-label">Solved by tag</div>', unsafe_allow_html=True)
            tag_df = cf_solved_by_tag(cf_data)
            if not tag_df.empty:
                st.plotly_chart(
                    styled_bar_chart(tag_df.head(10), "tag", "solved", ACCENT_CF, horizontal=True),
                    use_container_width=True,
                )

        st.markdown('<div class="section-label">Weak topics (attempted a lot, low solve rate)</div>', unsafe_allow_html=True)
        weak_df = cf_weak_tags(cf_data)
        st.dataframe(weak_df, use_container_width=True, hide_index=True)

    tab_idx += 1

# ---------- LeetCode tab ----------
if lc_data:
    with tabs[tab_idx]:
        lc_diff_df, total_solved = lc_solved_by_difficulty(lc_data)
        lc_tag_df = lc_top_tags(lc_data)

        st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        metric_card("Total Solved", str(int(total_solved)), ACCENT_LC, c1)
        metric_card("Username", lc_username or "—", ACCENT_LC, c2)
        top_tag = lc_tag_df.iloc[0]["tag"] if not lc_tag_df.empty else "—"
        metric_card("Top Tag", top_tag, ACCENT_LC, c3)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-label">Solved by difficulty</div>', unsafe_allow_html=True)
            st.plotly_chart(
                styled_bar_chart(lc_diff_df, "difficulty", "count", ACCENT_LC),
                use_container_width=True,
            )
        with col_b:
            st.markdown('<div class="section-label">Top tags</div>', unsafe_allow_html=True)
            st.plotly_chart(
                styled_bar_chart(lc_tag_df, "tag", "solved", ACCENT_LC, horizontal=True),
                use_container_width=True,
            )

    tab_idx += 1

# ---------- Contests tab ----------
if lc_contest_data and lc_contest_data.get("summary"):
    with tabs[tab_idx]:
        summary = lc_contest_data["summary"]
        contest_df = lc_contest_rating_df(lc_contest_data)

        st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        metric_card("Contest Rating", f"{summary['rating']:.0f}", ACCENT_CONTEST, c1)
        metric_card("Global Rank", f"#{summary['globalRanking']:,}", ACCENT_CONTEST, c2)
        metric_card("Contests Attended", str(summary["attendedContestsCount"]), ACCENT_CONTEST, c3)

        st.markdown('<div class="section-label">Rating history</div>', unsafe_allow_html=True)
        if not contest_df.empty:
            st.plotly_chart(
                styled_line_chart(contest_df, "date", "rating", ACCENT_CONTEST, hover_name="contest", y_title="Rating"),
                use_container_width=True,
            )

            st.markdown('<div class="section-label">Recent contests</div>', unsafe_allow_html=True)
            st.dataframe(
                contest_df[["contest", "date", "rank", "solved", "total", "rating"]]
                .sort_values("date", ascending=False)
                .reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )
elif lc_contest_data is not None and lc_data:
    st.info("No rated contest history found for this LeetCode username.")

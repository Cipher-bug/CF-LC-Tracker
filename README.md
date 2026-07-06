# CP Tracker — Codeforces + LeetCode Analytics Dashboard

A dashboard that pulls your Codeforces and LeetCode data and visualizes
rating progression, solved-problem breakdowns by tag/difficulty, and
identifies weak topics based on your actual submission history.

## Why this project

Most competitive programmers track progress manually or not at all. This
tool automates that: pull data from both platforms' public APIs, and get
a clear picture of where you're strong, where you're weak, and how your
rating has trended over time — instead of guessing.

## Features

- **Codeforces**
  - Rating history over time (line chart)
  - Solved problems bucketed by difficulty (e.g. 800–899, 1200–1299)
  - Solved problems by tag (graphs, dp, greedy, etc.)
  - **Weak topic detection**: tags with a high attempt count but low solve
    rate — a genuine signal of what to practice next, not just what you
    haven't touched yet.
- **LeetCode**
  - Total solved, broken down by Easy/Medium/Hard
  - Top tags by problems solved

## Architecture

```
fetch_data.py   -> pulls raw data from Codeforces API + LeetCode GraphQL,
                   saves to data/*.json (so you're not hitting the APIs
                   on every dashboard refresh)
analyze.py      -> pure functions that turn raw JSON into pandas
                   DataFrames the dashboard can plot directly
app.py          -> Streamlit dashboard that renders everything
```

Keeping fetch/analyze/display separate means each piece is independently
testable and easy to explain — e.g. in an interview you can walk through
exactly how the weak-topic logic works without touching the UI code.

## Setup

```bash
git clone <your-repo-url>
cd cf-leetcode-tracker
pip install -r requirements.txt

python fetch_data.py --cf-handle YOUR_CF_HANDLE --lc-username YOUR_LC_USERNAME

streamlit run app.py
```

This opens the dashboard in your browser at `localhost:8501`.

## Notes on the APIs used

- **Codeforces**: official public REST API (`codeforces.com/api/...`), no
  auth required. Documented at https://codeforces.com/apiHelp
- **LeetCode**: no official public API, but the site's own frontend uses a
  GraphQL endpoint (`leetcode.com/graphql`) that can be queried directly
  for public profile stats — this is the same approach used by most
  open-source LeetCode stats tools.

## Possible extensions

- Cache historical snapshots (e.g. daily) to track week-over-week
  improvement, not just a point-in-time snapshot
- Add a "recommended next problems" feature based on weak tags
- Deploy publicly via Streamlit Community Cloud

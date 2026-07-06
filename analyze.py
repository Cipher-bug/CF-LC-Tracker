"""
analyze.py
Turns raw Codeforces / LeetCode JSON (from fetch_data.py) into
clean pandas DataFrames / dicts that app.py can plot directly.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"


def load_codeforces():
    with open(DATA_DIR / "codeforces.json") as f:
        return json.load(f)


def load_leetcode():
    with open(DATA_DIR / "leetcode.json") as f:
        return json.load(f)


# ---------- Codeforces ----------

def cf_rating_history_df(cf_data: dict) -> pd.DataFrame:
    """Rating over time, one row per rated contest."""
    rows = []
    for entry in cf_data["rating_history"]:
        rows.append({
            "date": datetime.fromtimestamp(entry["ratingUpdateTimeSeconds"]),
            "contest": entry["contestName"],
            "rating": entry["newRating"],
        })
    return pd.DataFrame(rows).sort_values("date")


def cf_solved_by_tag(cf_data: dict) -> pd.DataFrame:
    """Count of uniquely solved problems per tag."""
    solved_problems = {}
    for sub in cf_data["submissions"]:
        if sub.get("verdict") == "OK":
            prob = sub["problem"]
            key = f"{prob.get('contestId')}-{prob.get('index')}"
            solved_problems[key] = prob  # dedupe by problem id

    tag_counts = defaultdict(int)
    for prob in solved_problems.values():
        for tag in prob.get("tags", []):
            tag_counts[tag] += 1

    df = pd.DataFrame(
        sorted(tag_counts.items(), key=lambda x: -x[1]),
        columns=["tag", "solved"],
    )
    return df


def cf_solved_by_difficulty(cf_data: dict) -> pd.DataFrame:
    """Bucket solved problems by CF rating (difficulty)."""
    solved_problems = {}
    for sub in cf_data["submissions"]:
        if sub.get("verdict") == "OK":
            prob = sub["problem"]
            key = f"{prob.get('contestId')}-{prob.get('index')}"
            solved_problems[key] = prob

    buckets = defaultdict(int)
    for prob in solved_problems.values():
        rating = prob.get("rating")
        if rating is None:
            buckets["Unrated"] += 1
        else:
            bucket = f"{(rating // 100) * 100}-{(rating // 100) * 100 + 99}"
            buckets[bucket] += 1

    df = pd.DataFrame(list(buckets.items()), columns=["difficulty", "solved"])
    return df


def cf_weak_tags(cf_data: dict, min_attempts: int = 3) -> pd.DataFrame:
    """
    Tags where you attempt a lot but solve relatively rarely.
    Useful for spotting genuine weak spots vs. tags you just haven't touched.
    """
    attempts = defaultdict(set)   # tag -> set of problem keys attempted
    solves = defaultdict(set)     # tag -> set of problem keys solved

    for sub in cf_data["submissions"]:
        prob = sub["problem"]
        key = f"{prob.get('contestId')}-{prob.get('index')}"
        for tag in prob.get("tags", []):
            attempts[tag].add(key)
            if sub.get("verdict") == "OK":
                solves[tag].add(key)

    rows = []
    for tag, attempted_set in attempts.items():
        n_attempts = len(attempted_set)
        n_solves = len(solves[tag])
        if n_attempts >= min_attempts:
            solve_rate = n_solves / n_attempts
            rows.append({
                "tag": tag,
                "attempted": n_attempts,
                "solved": n_solves,
                "solve_rate": round(solve_rate, 2),
            })

    df = pd.DataFrame(rows).sort_values("solve_rate")
    return df


# ---------- LeetCode ----------

def lc_solved_by_difficulty(lc_data: dict) -> pd.DataFrame:
    rows = lc_data["submitStatsGlobal"]["acSubmissionNum"]
    df = pd.DataFrame(rows)
    # LeetCode includes an "All" row; keep it separate
    return df[df["difficulty"] != "All"], df[df["difficulty"] == "All"]["count"].values[0]


def lc_top_tags(lc_data: dict, top_n: int = 10) -> pd.DataFrame:
    all_tags = []
    for level in ("fundamental", "intermediate", "advanced"):
        for entry in lc_data.get("tagProblemCounts", {}).get(level, []):
            all_tags.append({
                "tag": entry["tagName"],
                "solved": entry["problemsSolved"],
                "level": level,
            })
    df = pd.DataFrame(all_tags).sort_values("solved", ascending=False)
    return df.head(top_n)

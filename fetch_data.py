"""
fetch_data.py
Pulls competitive programming data for a given user from:
  - Codeforces public API
  - LeetCode public GraphQL endpoint

Saves raw JSON into data/ so analyze.py / app.py don't have to hit
the network every time you tweak the analysis.

Usage:
    python fetch_data.py --cf-handle CipherBug --lc-username CipherBug
"""

import argparse
import json
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CF_API = "https://codeforces.com/api"
LC_GRAPHQL = "https://leetcode.com/graphql"


def get_codeforces_data(handle: str) -> dict:
    """Fetch submissions + rating history for a Codeforces handle."""
    status_url = f"{CF_API}/user.status?handle={handle}"
    rating_url = f"{CF_API}/user.rating?handle={handle}"

    status_resp = requests.get(status_url, timeout=15).json()
    time.sleep(1)  # be polite to the CF API, avoid rate limiting
    rating_resp = requests.get(rating_url, timeout=15).json()

    if status_resp.get("status") != "OK":
        raise RuntimeError(f"Codeforces status API error: {status_resp}")
    if rating_resp.get("status") != "OK":
        raise RuntimeError(f"Codeforces rating API error: {rating_resp}")

    return {
        "submissions": status_resp["result"],
        "rating_history": rating_resp["result"],
    }


def get_leetcode_data(username: str) -> dict:
    """Fetch solved-count and tag stats for a LeetCode username."""
    query = """
    query userProfileStats($username: String!) {
      matchedUser(username: $username) {
        username
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
        tagProblemCounts {
          advanced { tagName problemsSolved }
          intermediate { tagName problemsSolved }
          fundamental { tagName problemsSolved }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {"username": username},
    }
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/{username}/",
    }
    resp = requests.post(LC_GRAPHQL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("data", {}).get("matchedUser"):
        raise RuntimeError(f"LeetCode user not found or API blocked response: {data}")

    return data["data"]["matchedUser"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cf-handle", default="CipherBug", help="Codeforces handle")
    parser.add_argument("--lc-username", default="CipherBug", help="LeetCode username")
    args = parser.parse_args()

    print(f"Fetching Codeforces data for '{args.cf_handle}'...")
    cf_data = get_codeforces_data(args.cf_handle)
    with open(DATA_DIR / "codeforces.json", "w") as f:
        json.dump(cf_data, f, indent=2)
    print(f"  -> saved {len(cf_data['submissions'])} submissions, "
          f"{len(cf_data['rating_history'])} rated contests.")

    print(f"Fetching LeetCode data for '{args.lc_username}'...")
    lc_data = get_leetcode_data(args.lc_username)
    with open(DATA_DIR / "leetcode.json", "w") as f:
        json.dump(lc_data, f, indent=2)
    print("  -> saved LeetCode stats.")

    print("\nDone. Run `streamlit run app.py` to view your dashboard.")


if __name__ == "__main__":
    main()

# CP Tracker

I got tired of manually checking my Codeforces and LeetCode profiles to see how I was actually doing, so I built this. A dashboard that pulls stats from both and shows rating trends, solved problems by tag/difficulty, and which topics I'm actually weak at (not just untouched).

## What it does

* Pulls your Codeforces rating history and plots it over time
* Breaks down solved problems by difficulty and by tag
* Figures out your genuinely weak topics, tags you've attempted a bunch but rarely solve, which is a better signal than just "0 solved" on tags you've never tried
* Same idea for LeetCode: solved count by difficulty, top tags
* Type in any handle/username in the sidebar and it fetches live, you don't need to be me to use it

## How it's built

Three files, each doing one thing:

* `fetch_data.py` talks to the Codeforces REST API and LeetCode's GraphQL endpoint and gets the raw data
* `analyze.py` takes that raw data and turns it into the numbers/tables the dashboard actually needs
* `app.py` is the Streamlit UI, wires everything together

Splitting it up this way made debugging way easier. When something broke, I always knew which file to look in.

## Running it

```bash
git clone <your-repo-url>
cd cf-leetcode-tracker
pip install -r requirements.txt
streamlit run app.py
```

Opens at `localhost:8501`. Enter a Codeforces handle and/or LeetCode username in the sidebar, hit **Fetch stats**.

If you'd rather pull data via the terminal instead of the UI (e.g. to save it to a file):
```bash
python fetch_data.py --cf-handle YOUR_CF_HANDLE --lc-username YOUR_LC_USERNAME
```

## A note on the APIs

Codeforces has an actual public API, well documented, no auth needed. LeetCode doesn't officially expose one, but their site quietly uses a GraphQL endpoint internally that you can query directly for public profile data. Pretty common trick, a lot of LeetCode stats tools out there use the same approach.

## Ideas for later

* Track stats over time instead of just a snapshot (would need to store daily/weekly history)
* Suggest problems to try next based on weak topics
* Deploy it properly so I don't need to run it locally every time

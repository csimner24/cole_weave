"""
Weave Data Collection Script
Fetches PostHog/posthog GitHub data via GraphQL API for the last 100 days.
Outputs JSON files to data/ for the dashboard.

Usage:
    set GITHUB_TOKEN=ghp_...
    python scripts/collect.py
"""

import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

REPO_OWNER = "PostHog"
REPO_NAME = "posthog"
DAYS_BACK = 100
GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"


def get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    print("ERROR: No GitHub token found.")
    print("Set GITHUB_TOKEN as an environment variable or add it to .env")
    print("  PowerShell: $env:GITHUB_TOKEN = 'ghp_...'")
    print("  Bash/WSL:   export GITHUB_TOKEN=ghp_...")
    sys.exit(1)


def make_session(token):
    session = requests.Session()
    session.headers.update({
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    })
    return session


def graphql_query(session, query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    for attempt in range(4):
        resp = session.post(GRAPHQL_URL, json=payload)

        remaining = int(resp.headers.get("x-ratelimit-remaining", 5000))
        if remaining < 50:
            reset_at = int(resp.headers.get("x-ratelimit-reset", 0))
            sleep_for = max(reset_at - time.time() + 2, 1)
            print(f"  Rate limit low ({remaining} remaining), sleeping {sleep_for:.0f}s...")
            time.sleep(sleep_for)

        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                print(f"  GraphQL errors: {data['errors']}")
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
            return data.get("data")

        if resp.status_code in (502, 503) and attempt < 3:
            time.sleep(2 ** attempt)
            continue

        print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
        if attempt < 3:
            time.sleep(2 ** attempt)
        else:
            return None

    return None


def rest_get(session, endpoint):
    url = f"{REST_URL}{endpoint}"
    for attempt in range(4):
        resp = session.get(url)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (502, 503) and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        print(f"  REST {resp.status_code} on {endpoint}: {resp.text[:200]}")
        return None
    return None


# ---------------------------------------------------------------------------
# Phase 1: Merged PRs via search, then fetch details in batches
# ---------------------------------------------------------------------------

PR_SEARCH_QUERY = """
query($query: String!, $cursor: String) {
  search(query: $query, type: ISSUE, first: 25, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    issueCount
    nodes {
      ... on PullRequest {
        number
        title
        additions
        deletions
        changedFiles
        mergedAt
        createdAt
        author { login }
        labels(first: 15) { nodes { name } }
        body
        reviews(first: 50) {
          nodes { author { login } state }
        }
        files(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes { path additions deletions }
        }
      }
    }
  }
}
"""

PR_FILES_QUERY = """
query($prNumber: Int!, $cursor: String) {
  repository(owner: "PostHog", name: "posthog") {
    pullRequest(number: $prNumber) {
      files(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { path additions deletions }
      }
    }
  }
}
"""


def _search_prs_window(session, start_date, end_date):
    """Search for merged PRs in a specific date window. Returns list of PR dicts."""
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    search_q = f"repo:PostHog/posthog is:pr is:merged merged:{start_str}..{end_str}"

    prs = []
    cursor = None

    while True:
        data = graphql_query(session, PR_SEARCH_QUERY, {"query": search_q, "cursor": cursor})
        if not data:
            break

        search_data = data["search"]
        nodes = search_data["nodes"]
        total_count = search_data.get("issueCount", 0)

        for pr in nodes:
            if not pr or not pr.get("number"):
                continue

            files_list = [f for f in (pr.get("files", {}).get("nodes") or [])]
            files_page_info = pr.get("files", {}).get("pageInfo", {})
            if files_page_info.get("hasNextPage"):
                fc = files_page_info["endCursor"]
                while True:
                    fd = graphql_query(session, PR_FILES_QUERY,
                                       {"prNumber": pr["number"], "cursor": fc})
                    if not fd:
                        break
                    extra = fd["repository"]["pullRequest"]["files"]
                    files_list.extend(extra["nodes"])
                    if not extra["pageInfo"]["hasNextPage"]:
                        break
                    fc = extra["pageInfo"]["endCursor"]

            prs.append({
                "number": pr["number"],
                "title": pr["title"],
                "author": (pr.get("author") or {}).get("login"),
                "additions": pr["additions"],
                "deletions": pr["deletions"],
                "changed_files": pr["changedFiles"],
                "merged_at": pr["mergedAt"],
                "created_at": pr["createdAt"],
                "labels": [l["name"] for l in (pr.get("labels", {}).get("nodes") or [])],
                "body_length": len(pr.get("body") or ""),
                "reviews": [
                    {"reviewer": (r.get("author") or {}).get("login"), "state": r["state"]}
                    for r in (pr.get("reviews", {}).get("nodes") or [])
                ],
                "files": [
                    {"path": f["path"], "additions": f["additions"], "deletions": f["deletions"]}
                    for f in files_list
                ],
            })

        if not search_data["pageInfo"]["hasNextPage"]:
            break
        cursor = search_data["pageInfo"]["endCursor"]

        if len(prs) >= 950 and total_count > 1000:
            print(f"    WARNING: Window {start_str}..{end_str} has {total_count} results (capped at 1000)")
            break

    return prs, total_count


def fetch_prs(session, since_date):
    print("Phase 1: Fetching merged PRs via search (chunked by 10-day windows)...")
    now = datetime.now(timezone.utc)
    all_prs = []
    seen_numbers = set()

    window_start = since_date
    chunk_days = 10

    while window_start < now:
        window_end = min(window_start + timedelta(days=chunk_days), now)
        start_str = window_start.strftime("%Y-%m-%d")
        end_str = window_end.strftime("%Y-%m-%d")

        prs, total_in_window = _search_prs_window(session, window_start, window_end)

        new_prs = [p for p in prs if p["number"] not in seen_numbers]
        for p in new_prs:
            seen_numbers.add(p["number"])
        all_prs.extend(new_prs)

        print(f"  Window {start_str} to {end_str}: {len(new_prs)} new PRs (running total: {len(all_prs)})")

        window_start = window_end

    print(f"  Total merged PRs in window: {len(all_prs)}")
    return all_prs


# ---------------------------------------------------------------------------
# Phase 2: Commits (GraphQL paginated)
# ---------------------------------------------------------------------------

COMMITS_QUERY = """
query($since: GitTimestamp!, $cursor: String) {
  repository(owner: "PostHog", name: "posthog") {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor, since: $since) {
            pageInfo { hasNextPage endCursor }
            totalCount
            nodes {
              oid
              message
              author { user { login } name date }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_commits(session, since_iso):
    print("Phase 2: Fetching commits...")
    all_commits = []
    cursor = None
    page = 0

    while True:
        page += 1
        data = graphql_query(session, COMMITS_QUERY, {"since": since_iso, "cursor": cursor})
        if not data:
            print("  Failed to fetch commits, stopping.")
            break

        history = data["repository"]["defaultBranchRef"]["target"]["history"]
        nodes = history["nodes"]

        for c in nodes:
            author_user = (c.get("author") or {}).get("user")
            all_commits.append({
                "sha": c["oid"][:12],
                "login": author_user.get("login") if author_user else None,
                "name": (c.get("author") or {}).get("name"),
                "date": (c.get("author") or {}).get("date"),
                "message": (c.get("message") or "").split("\n")[0],
            })

        print(f"  Page {page}: {len(nodes)} commits (total: {len(all_commits)} / {history.get('totalCount', '?')})")

        if not history["pageInfo"]["hasNextPage"]:
            break
        cursor = history["pageInfo"]["endCursor"]

    print(f"  Total commits in window: {len(all_commits)}")
    return all_commits


# ---------------------------------------------------------------------------
# Phase 3: Issues with close events (GraphQL batched)
# ---------------------------------------------------------------------------

ISSUES_QUERY = """
query($since: DateTime!, $cursor: String) {
  repository(owner: "PostHog", name: "posthog") {
    issues(first: 50, after: $cursor,
           filterBy: {since: $since}, states: [OPEN, CLOSED],
           orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        state
        author { login }
        createdAt
        closedAt
        labels(first: 15) { nodes { name } }
        timelineItems(itemTypes: [CLOSED_EVENT], first: 5) {
          nodes {
            ... on ClosedEvent {
              actor { login }
              createdAt
            }
          }
        }
      }
    }
  }
}
"""


def fetch_issues(session, since_iso):
    print("Phase 3: Fetching issues with close events...")
    all_issues = []
    cursor = None
    page = 0

    while True:
        page += 1
        data = graphql_query(session, ISSUES_QUERY, {"since": since_iso, "cursor": cursor})
        if not data:
            print("  Failed to fetch issues, stopping.")
            break

        issue_data = data["repository"]["issues"]
        nodes = issue_data["nodes"]

        for issue in nodes:
            labels = [l["name"] for l in (issue.get("labels", {}).get("nodes") or [])]
            timeline = issue.get("timelineItems", {}).get("nodes") or []
            closer = None
            for evt in timeline:
                if evt and evt.get("actor"):
                    closer = evt["actor"].get("login")
                    break

            all_issues.append({
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "author": (issue.get("author") or {}).get("login"),
                "created_at": issue["createdAt"],
                "closed_at": issue.get("closedAt"),
                "labels": labels,
                "closer": closer,
            })

        print(f"  Page {page}: {len(nodes)} issues (total: {len(all_issues)})")

        if not issue_data["pageInfo"]["hasNextPage"]:
            break
        cursor = issue_data["pageInfo"]["endCursor"]

    print(f"  Total issues in window: {len(all_issues)}")
    return all_issues


# ---------------------------------------------------------------------------
# Phase 3b: Git tree for total file count (REST)
# ---------------------------------------------------------------------------

def fetch_total_files(session):
    print("Phase 3b: Fetching git tree for total file count...")
    data = rest_get(session, f"/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/master?recursive=true")
    if not data:
        print("  Failed to fetch tree, defaulting to 0")
        return 0
    total = sum(1 for entry in data.get("tree", []) if entry.get("type") == "blob")
    print(f"  Total files in repo: {total}")
    if data.get("truncated"):
        print("  WARNING: Tree was truncated, file count may be incomplete")
    return total


# ---------------------------------------------------------------------------
# Phase 4: Aggregation
# ---------------------------------------------------------------------------

PRIORITY_LABELS = {"P0", "P1", "P2", "P3++"}
COMMIT_TYPE_RE = re.compile(r"^(feat|fix|chore|refactor|docs|test|ci|perf|style|build|revert)\b", re.IGNORECASE)


def aggregate(prs, commits, issues, total_files):
    print("Phase 4: Aggregating metrics per engineer...")

    engineers = defaultdict(lambda: {
        "username": None,
        "commits": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "prs_merged": 0,
        "feat_count": 0,
        "fix_count": 0,
        "chore_count": 0,
        "reviews_approved": 0,
        "reviews_commented": 0,
        "bugs_fixed_all": 0,
        "p0_bugs_fixed": 0,
        "issues_opened": 0,
        "issues_closed": 0,
        "files_edited": 0,
        "files_edited_pct": 0.0,
        "directories_touched": 0,
        "cross_team_pct": 0.0,
        "engineer_score": 0,
    })

    dir_coverage = defaultdict(set)
    file_coverage = defaultdict(set)
    dir_file_counts = defaultdict(lambda: defaultdict(int))

    # --- PRs: volume, commit type, reviews, files ---
    for pr in prs:
        author = pr["author"]
        if not author:
            continue

        eng = engineers[author]
        eng["username"] = author
        eng["prs_merged"] += 1
        eng["lines_added"] += pr["additions"]
        eng["lines_deleted"] += pr["deletions"]

        title = pr["title"].strip()
        m = COMMIT_TYPE_RE.match(title)
        if m:
            ctype = m.group(1).lower()
            if ctype == "feat":
                eng["feat_count"] += 1
            elif ctype == "fix":
                eng["fix_count"] += 1
            elif ctype == "chore":
                eng["chore_count"] += 1

        for review in pr["reviews"]:
            reviewer = review["reviewer"]
            if not reviewer:
                continue
            state = review["state"]
            r_eng = engineers[reviewer]
            r_eng["username"] = reviewer
            if state == "APPROVED":
                r_eng["reviews_approved"] += 1
            elif state == "COMMENTED":
                r_eng["reviews_commented"] += 1

        for f in pr["files"]:
            path = f["path"]
            file_coverage[author].add(path)
            top_dir = path.split("/")[0] if "/" in path else "root"
            dir_coverage[author].add(top_dir)
            dir_file_counts[author][top_dir] += 1

    # --- Commits ---
    for c in commits:
        login = c["login"]
        if not login:
            continue
        eng = engineers[login]
        eng["username"] = login
        eng["commits"] += 1

    # --- Issues ---
    for issue in issues:
        author = issue["author"]
        if author:
            engineers[author]["username"] = author
            engineers[author]["issues_opened"] += 1

        closer = issue["closer"]
        if closer and issue["state"] == "CLOSED":
            engineers[closer]["username"] = closer
            engineers[closer]["issues_closed"] += 1

            labels = set(issue["labels"])
            is_bug = "bug" in labels

            if is_bug:
                engineers[closer]["bugs_fixed_all"] += 1
                if "P0" in labels:
                    engineers[closer]["p0_bugs_fixed"] += 1

    # --- Files edited, breadth, cross-team ---
    for author, files in file_coverage.items():
        eng = engineers[author]
        eng["files_edited"] = len(files)
        eng["files_edited_pct"] = round(len(files) / total_files * 100, 2) if total_files > 0 else 0

    for author, dirs in dir_coverage.items():
        engineers[author]["directories_touched"] = len(dirs)

    for author, dir_counts in dir_file_counts.items():
        if not dir_counts:
            continue
        primary_dir = max(dir_counts, key=dir_counts.get)
        total_edits = sum(dir_counts.values())
        other_edits = total_edits - dir_counts[primary_dir]
        engineers[author]["cross_team_pct"] = round(other_edits / total_edits * 100, 1) if total_edits > 0 else 0

    # --- Engineer Score ---
    for eng in engineers.values():
        volume = eng["commits"] + eng["lines_added"] + eng["lines_deleted"]
        eng["engineer_score"] = (
            (1 + volume)
            * (1 + eng["issues_closed"])
            * (1 + eng["directories_touched"])
        )

    result = sorted(engineers.values(), key=lambda e: e["engineer_score"], reverse=True)
    print(f"  Total engineers: {len(result)}")
    return result, dict(dir_coverage), dict(dir_file_counts)


# ---------------------------------------------------------------------------
# Phase 5: Write JSON output
# ---------------------------------------------------------------------------

def write_output(engineers, dir_coverage, dir_file_counts, meta):
    print("Phase 5: Writing JSON data files...")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_DIR / "engineers.json", "w") as f:
        json.dump(engineers, f, indent=2, default=str)

    coverage_serializable = {k: sorted(v) for k, v in dir_coverage.items()}
    with open(DATA_DIR / "directory_coverage.json", "w") as f:
        json.dump(coverage_serializable, f, indent=2)

    with open(DATA_DIR / "cross_team_details.json", "w") as f:
        json.dump(dir_file_counts, f, indent=2)

    with open(DATA_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Written to {DATA_DIR}/")
    print(f"    engineers.json        ({len(engineers)} engineers)")
    print(f"    directory_coverage.json")
    print(f"    cross_team_details.json")
    print(f"    meta.json")


def save_raw(name, data):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / f"{name}.json", "w") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    start_time = time.time()
    print("=" * 60)
    print("Weave Data Collection - PostHog/posthog")
    print("=" * 60)

    token = get_token()
    session = make_session(token)

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=DAYS_BACK)
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Date range: {since.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')} ({DAYS_BACK} days)")
    print()

    # Check rate limit
    rl = rest_get(session, "/rate_limit")
    if rl:
        graphql_rl = rl.get("resources", {}).get("graphql", {})
        print(f"GraphQL rate limit: {graphql_rl.get('remaining', '?')}/{graphql_rl.get('limit', '?')}")
    print()

    prs = fetch_prs(session, since)
    save_raw("pulls", prs)
    print()

    commits = fetch_commits(session, since_iso)
    save_raw("commits", commits)
    print()

    issues = fetch_issues(session, since_iso)
    save_raw("issues", issues)
    print()

    total_files = fetch_total_files(session)
    print()

    engineers, dir_coverage, dir_file_counts = aggregate(prs, commits, issues, total_files)
    print()

    meta = {
        "collected_at": now.isoformat(),
        "since": since.isoformat(),
        "days_back": DAYS_BACK,
        "total_prs": len(prs),
        "total_commits": len(commits),
        "total_issues": len(issues),
        "total_repo_files": total_files,
        "total_engineers": len(engineers),
    }

    write_output(engineers, dir_coverage, dir_file_counts, meta)

    elapsed = time.time() - start_time
    print()
    print(f"Done in {elapsed:.1f}s")

    top5 = engineers[:5]
    print()
    print("Top 5 Engineers by Score:")
    for i, eng in enumerate(top5, 1):
        print(f"  {i}. {eng['username']}: score={eng['engineer_score']:,.0f}  "
              f"(volume={eng['commits'] + eng['lines_added'] + eng['lines_deleted']}, "
              f"p0_bugs={eng['p0_bugs_fixed']}, "
              f"issues_closed={eng['issues_closed']}, "
              f"breadth={eng['directories_touched']})")


if __name__ == "__main__":
    main()

# Weave - PostHog Engineer Impact Dashboard

## Overview

Weave helps engineering teams understand their productivity and impact. This project analyzes real GitHub data from the [PostHog repository](https://github.com/PostHog/posthog) to identify the most impactful engineers and present findings on a single-page interactive dashboard.

**Target audience:** A busy engineering leader on the PostHog team who understands the basics but isn't in the weeds enough to read every PR or line of code.

**Deployment:** Hosted on Vercel.

**Key constraint:** An ugly UI with creative analysis is better than a beautiful UI with simple metrics like LOC or commit counts alone.

## Data Source

- Repository: `PostHog/posthog`
- Time window: Last 100 days
- Languages in repo: Python (51.4%), TypeScript (39.5%), Rust (7%), JavaScript (0.5%), Go (0.5%), SCSS (0.3%)

## Data Architecture

- Pre-fetch all GitHub data during a build/collection step
- Store metric data in a local database within the project
- Dashboard reads from the local database so it loads quickly on Vercel
- No live GitHub API calls from the deployed dashboard

## Impact Metrics (Confirmed)

### 1. Volume (Balanced)

- Number of commits per author
- Lines added + deleted per author (sourced from PR-level `additions`/`deletions` fields)

### 2. PR & Commit Quality

- Parse conventional commit type from PR titles (`feat(scope):`, `fix(scope):`, `chore(scope):`)

### 3a. Code Reviews (Approved)

- Number of APPROVED reviews given per engineer
- Any PostHog engineer can review most PRs (confirmed -- not restricted to seniors)
- Source: `GET /pulls/{n}/reviews` per merged PR, filtered to `state: APPROVED`

### 3b. Code Reviews (Commented)

- Number of COMMENTED reviews given per engineer
- Source: `GET /pulls/{n}/reviews` per merged PR, filtered to `state: COMMENTED`

### 4a. Bugs Fixed (All Priorities)

- Who closes the most bug issues across all priorities (P0-P3)
- Source: `GET /issues/{n}/events` to identify closer, filtered to issues with `bug` + any P0-P3 label
- Limited to 100-day window

### 4b. P0 Bugs Fixed

- Who closes the most P0-labeled bug issues specifically
- Source: same as 4a, filtered to `P0` label only

### 4c. Issues Opened / Closed

- Who opens the most issues (from `GET /issues?since=...&state=all`)
- Who closes the most issues (from `GET /issues/{n}/events`)
- Issue categorization via labels: `bug`, `enhancement`, `question`, `feature/*`, `team/*`

### 5a. Files Edited (Count)

- Total unique files edited per author (from `GET /pulls/{n}/files`)

### 5b. Files Edited (% of Repo)

- Unique files edited as a percentage of total repo files
- Denominator from `GET /git/trees/master?recursive=true`

### 6. Breadth / Directory Coverage

- Number of distinct top-level directories each author commits to
- Measures cross-functional scope and versatility
- Source: parse `filename` paths from `GET /pulls/{n}/files`


### 7. Cross-Team Contributions

- Detect contributions outside an engineer's primary team area
- Use `team/*` labels on PRs/issues or directory-based heuristics (e.g., frontend/ vs rust/ vs posthog/)
- Shows engineers who contribute beyond their team

### Explicitly Excluded

- Sole-editor file ownership %
- PR size distribution
- Lines modified over time (trend charts)
- Time to merge
- Bot filtering (bots will appear in data but we won't add special filtering logic)
- PR discussion depth / comment counts on PRs
- Bug author vs bug fixer cross-referencing
- Architecture-related commit heuristics
- File creation tracking (first commit per file path)
- CHANGES_REQUESTED review type

## Impact Score Definition

The "Engineer Score" answers: **"Who are the most impactful engineers at PostHog?"**

### Formula

```
Engineer Score = Volume × P0 Bugs Fixed × Issues Closed × Breadth
```

Where:
- **Volume** = `commits + (lines_added + lines_deleted)` -- balances commit frequency with code output
- **P0 Bugs Fixed** = `p0_bugs_fixed` -- number of critical (P0) bug issues closed
- **Issues Closed** = `issues_closed` -- total issues closed by the engineer
- **Breadth** = `directories_touched` -- distinct top-level directories committed to

**Zero-product note:** If an engineer has 0 in any factor, their score is 0. To avoid this, the computation uses `(1 + value)` for each factor so that missing activity in one dimension reduces but does not eliminate the score:

```
Engineer Score = (1 + Volume) × (1 + P0 Bugs Fixed) × (1 + Issues Closed) × (1 + Breadth)
```

## Dashboard Requirements

- Single page, fits on a laptop screen
- Interactive
- Hosted on Vercel

## Implementation Details

### Data Model

All data is organized per engineer. The primary key (UID) is the GitHub username (commit author login). Each engineer is a single row in the main table with columns for each metric.

### Engineer Table (one row per author)

| Column | Source Metric | Type |
|--------|---------------|------|
| `username` | GitHub login (UID) | string |
| `commits` | Total commits authored (1) | number |
| `lines_added` | Total lines added across merged PRs (1) | number |
| `lines_deleted` | Total lines deleted across merged PRs (1) | number |
| `prs_merged` | Total PRs merged (1) | number |
| `feat_count` | PRs with `feat(...)` title prefix (2) | number |
| `fix_count` | PRs with `fix(...)` title prefix (2) | number |
| `chore_count` | PRs with `chore(...)` title prefix (2) | number |
| `reviews_approved` | Reviews with APPROVED state (3a) | number |
| `reviews_commented` | Reviews with COMMENTED state (3b) | number |
| `bugs_fixed_all` | Bug issues closed across P0-P3 (4a) | number |
| `p0_bugs_fixed` | P0-labeled bug issues closed (4b) | number |
| `issues_opened` | Issues authored (4c) | number |
| `issues_closed` | Issues closed (4c) | number |
| `files_edited` | Unique files touched (5a) | number |
| `files_edited_pct` | As % of total repo files (5b) | number (0-100) |
| `directories_touched` | Distinct top-level directories (6) | number |
| `cross_team_pct` | % of contributions outside primary team area (7) | number (0-100) |
| `engineer_score` | Computed: (1+Volume) x (1+P0 Bugs) x (1+Issues Closed) x (1+Breadth) | number |

### Dashboard Layout (top to bottom)

#### 1. Leaderboard: "Engineer Score - Who Are the Most Impactful Engineers at PostHog?"

- Ranked table showing the **top 5** engineers sorted by `engineer_score` descending
- Shows each engineer's score and the 4 component values (Volume, P0 Bugs Fixed, Issues Closed, Breadth)
- Hover tooltip on the leaderboard title shows the formula and a text description of what the score measures

#### 2. Methodology Banner

A text banner below the leaderboard explaining why these four dimensions define impact:

> "Impact isn't just about writing code -- it's about the right code, at the right time, across the right surface area. We measure four dimensions that together capture what makes an engineer indispensable. **Volume** reflects sustained output: the commits shipped and lines changed through peer-reviewed pull requests. **P0 Bugs Fixed** measures reliability under pressure: who steps up when the product is broken and users are affected. **Issues Closed** captures follow-through: the ability to take problems from identification to resolution, not just file them but finish them. **Breadth** reveals architectural range: engineers who contribute across multiple areas of the codebase rather than staying siloed in a single corner. An engineer who scores highly across all four isn't just busy -- they're the kind of person the team can't afford to lose."

#### 3. Four Primary Bar Charts (side by side)

Each chart is a horizontal or vertical bar chart showing the top engineers for that metric.

| Chart | Metric | Formula shown on chart | Hover description |
|-------|--------|----------------------|-------------------|
| **Volume** | `commits + (lines_added + lines_deleted)` | `Volume = commits + lines_added + lines_deleted` | "Total code output: number of commits plus total lines added and deleted across merged PRs. Balances engineers who make many small changes with those who make fewer large changes." |
| **P0 Bugs Fixed** | `p0_bugs_fixed` | `P0 Bugs Fixed = count of closed P0-labeled bug issues` | "Number of critical (P0) bug issues this engineer closed. P0 bugs are page crashes, missing functionality, and breaking issues." |
| **Issues Closed** | `issues_closed` | `Issues Closed = count of issues closed by engineer` | "Total issues closed by this engineer across all types and priorities. Indicates responsiveness and problem-solving throughput." |
| **Breadth** | `directories_touched` | `Breadth = count of distinct top-level directories` | "Number of distinct top-level directories this engineer committed to. Higher breadth indicates cross-functional scope and versatility across the codebase." |

#### 4. Full Engineer Data Table

- Sortable table with all columns from the Engineer Table above
- One row per engineer, every metric visible
- Dashboard user can sort by any column to explore the data

### Supplementary Data for Charts

Metrics that have richer detail than a single scalar are stored in supplementary tables in the local database:

- **Breadth / Directory Coverage:** Per-author list of directory names, used to render a heatmap or breakdown chart.
- **Cross-Team Contributions:** Per-author breakdown of which team areas they contributed to, used for a stacked bar or pie chart.

## Data Pipeline

All data is precomputed and stored in a local database. The dashboard reads from this database at runtime -- no live GitHub API calls. Data covers a **100-day window**.

### API Endpoints Used

| Endpoint | Purpose | Call volume |
|----------|---------|-------------|
| `GET /repos/{owner}/{repo}/pulls?state=closed` | PR list with additions/deletions/labels/body | ~15 pages |
| `GET /repos/{owner}/{repo}/pulls/{n}/reviews` | Reviews per PR | ~1 per PR |
| `GET /repos/{owner}/{repo}/pulls/{n}/files` | Files changed per PR (for breadth, files edited, ownership) | ~1 per PR |
| `GET /repos/{owner}/{repo}/commits?since=` | Commit list with author/date/message | ~30 pages |
| `GET /repos/{owner}/{repo}/issues?since=&state=all` | Issues with labels, author, dates | ~30 pages |
| `GET /repos/{owner}/{repo}/issues/{n}/events` | Who closed each issue | ~1 per issue |
| `GET /repos/{owner}/{repo}/git/trees/master?recursive=true` | Total file count in repo | 1 call |

### Database Tables

| Table | Contents |
|-------|----------|
| `engineers` | One row per author with all scalar metrics (see Engineer Table above) |
| `directory_coverage` | Per-author list of directories touched (for breadth chart drill-down) |
| `cross_team_details` | Per-author breakdown of team areas contributed to (for cross-team chart) |

### Collection Script

The script (`scripts/collect.py` or `scripts/collect.ts`):
1. Authenticates with the GitHub API using a personal access token
2. Paginates through all relevant endpoints for the last 100 days
3. Aggregates and computes metrics per author
4. Writes the results to the local database

Estimated API budget: ~3,000-3,500 calls (fits within the 5,000/hr rate limit with a PAT).

To refresh data, re-run the script and redeploy.

## Project Phases

1. **Explore available metrics** - Investigate what data the GitHub API provides, how PostHog labels issues, review policies, etc.
2. **Data collection** - Build scripts to fetch and process GitHub data into the local database
3. **Analysis** - Compute impact scores from the raw data, store in the database
4. **Dashboard** - Build the interactive single-page dashboard that reads from the local database
5. **Deploy** - Host on Vercel

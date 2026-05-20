import type { Engineer, CollectionMeta } from "@/types/engineer";

function computeScore(e: Omit<Engineer, "engineer_score">): number {
  const volume = e.commits + e.lines_added + e.lines_deleted;
  return (1 + volume) * (1 + e.issues_closed) * (1 + e.directories_touched);
}

function makeEngineer(partial: Omit<Engineer, "engineer_score">): Engineer {
  return { ...partial, engineer_score: computeScore(partial) };
}

const MOCK_ENGINEERS: Engineer[] = [
  makeEngineer({ username: "alice-dev", commits: 312, lines_added: 18420, lines_deleted: 9210, prs_merged: 87, feat_count: 34, fix_count: 28, chore_count: 15, reviews_approved: 64, reviews_commented: 41, bugs_fixed_all: 12, p0_bugs_fixed: 4, issues_opened: 45, issues_closed: 52, files_edited: 834, files_edited_pct: 5.2, directories_touched: 18, cross_team_pct: 42.1 }),
  makeEngineer({ username: "bob-eng", commits: 245, lines_added: 14300, lines_deleted: 7100, prs_merged: 68, feat_count: 22, fix_count: 31, chore_count: 10, reviews_approved: 92, reviews_commented: 58, bugs_fixed_all: 18, p0_bugs_fixed: 6, issues_opened: 38, issues_closed: 61, files_edited: 612, files_edited_pct: 3.8, directories_touched: 15, cross_team_pct: 35.7 }),
  makeEngineer({ username: "carol-hog", commits: 189, lines_added: 22100, lines_deleted: 11400, prs_merged: 52, feat_count: 18, fix_count: 14, chore_count: 12, reviews_approved: 47, reviews_commented: 33, bugs_fixed_all: 8, p0_bugs_fixed: 2, issues_opened: 29, issues_closed: 34, files_edited: 920, files_edited_pct: 5.7, directories_touched: 22, cross_team_pct: 55.3 }),
  makeEngineer({ username: "dave-ops", commits: 156, lines_added: 8900, lines_deleted: 4200, prs_merged: 41, feat_count: 8, fix_count: 22, chore_count: 7, reviews_approved: 110, reviews_commented: 72, bugs_fixed_all: 24, p0_bugs_fixed: 9, issues_opened: 62, issues_closed: 78, files_edited: 445, files_edited_pct: 2.8, directories_touched: 12, cross_team_pct: 28.4 }),
  makeEngineer({ username: "eve-frontend", commits: 278, lines_added: 16700, lines_deleted: 8300, prs_merged: 74, feat_count: 42, fix_count: 18, chore_count: 8, reviews_approved: 55, reviews_commented: 29, bugs_fixed_all: 6, p0_bugs_fixed: 1, issues_opened: 33, issues_closed: 28, files_edited: 710, files_edited_pct: 4.4, directories_touched: 9, cross_team_pct: 15.2 }),
  makeEngineer({ username: "frank-rust", commits: 134, lines_added: 11200, lines_deleted: 5600, prs_merged: 38, feat_count: 15, fix_count: 12, chore_count: 6, reviews_approved: 38, reviews_commented: 22, bugs_fixed_all: 10, p0_bugs_fixed: 3, issues_opened: 21, issues_closed: 42, files_edited: 380, files_edited_pct: 2.4, directories_touched: 14, cross_team_pct: 48.9 }),
  makeEngineer({ username: "grace-data", commits: 98, lines_added: 7400, lines_deleted: 3100, prs_merged: 29, feat_count: 10, fix_count: 8, chore_count: 9, reviews_approved: 25, reviews_commented: 18, bugs_fixed_all: 5, p0_bugs_fixed: 1, issues_opened: 18, issues_closed: 22, files_edited: 290, files_edited_pct: 1.8, directories_touched: 8, cross_team_pct: 22.0 }),
  makeEngineer({ username: "hank-infra", commits: 201, lines_added: 5200, lines_deleted: 2800, prs_merged: 55, feat_count: 6, fix_count: 35, chore_count: 11, reviews_approved: 78, reviews_commented: 45, bugs_fixed_all: 15, p0_bugs_fixed: 5, issues_opened: 48, issues_closed: 55, files_edited: 320, files_edited_pct: 2.0, directories_touched: 11, cross_team_pct: 31.6 }),
  makeEngineer({ username: "iris-qa", commits: 67, lines_added: 3200, lines_deleted: 1800, prs_merged: 22, feat_count: 3, fix_count: 14, chore_count: 4, reviews_approved: 145, reviews_commented: 88, bugs_fixed_all: 20, p0_bugs_fixed: 7, issues_opened: 85, issues_closed: 68, files_edited: 210, files_edited_pct: 1.3, directories_touched: 7, cross_team_pct: 18.5 }),
  makeEngineer({ username: "jake-mobile", commits: 112, lines_added: 9800, lines_deleted: 4100, prs_merged: 34, feat_count: 20, fix_count: 9, chore_count: 3, reviews_approved: 30, reviews_commented: 15, bugs_fixed_all: 3, p0_bugs_fixed: 0, issues_opened: 14, issues_closed: 19, files_edited: 410, files_edited_pct: 2.6, directories_touched: 6, cross_team_pct: 12.8 }),
].sort((a, b) => b.engineer_score - a.engineer_score);

const MOCK_META: CollectionMeta = {
  collected_at: new Date().toISOString(),
  since: new Date(Date.now() - 100 * 86400000).toISOString(),
  days_back: 100,
  total_prs: 485,
  total_commits: 1792,
  total_issues: 1240,
  total_repo_files: 16042,
  total_engineers: 10,
};

async function loadJson<T>(path: string): Promise<T | null> {
  try {
    const fs = await import("fs/promises");
    const p = await import("path");
    const filePath = p.join(process.cwd(), path);
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export async function getEngineers(): Promise<Engineer[]> {
  const data = await loadJson<Engineer[]>("data/engineers.json");
  return data ?? MOCK_ENGINEERS;
}

export async function getMeta(): Promise<CollectionMeta> {
  const data = await loadJson<CollectionMeta>("data/meta.json");
  return data ?? MOCK_META;
}

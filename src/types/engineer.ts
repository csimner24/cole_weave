export interface Engineer {
  username: string;
  commits: number;
  lines_added: number;
  lines_deleted: number;
  prs_merged: number;
  feat_count: number;
  fix_count: number;
  chore_count: number;
  reviews_approved: number;
  reviews_commented: number;
  bugs_fixed_all: number;
  p0_bugs_fixed: number;
  issues_opened: number;
  issues_closed: number;
  files_edited: number;
  files_edited_pct: number;
  directories_touched: number;
  cross_team_pct: number;
  engineer_score: number;
}

export interface CollectionMeta {
  collected_at: string;
  since: string;
  days_back: number;
  total_prs: number;
  total_commits: number;
  total_issues: number;
  total_repo_files: number;
  total_engineers: number;
}

export type DirectoryCoverage = Record<string, string[]>;

export type CrossTeamDetails = Record<string, Record<string, number>>;

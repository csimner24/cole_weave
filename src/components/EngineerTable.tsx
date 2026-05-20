"use client";

import { useState, useMemo } from "react";
import type { Engineer } from "@/types/engineer";

type SortKey = keyof Engineer;
type SortDir = "asc" | "desc";

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "username", label: "Engineer" },
  { key: "engineer_score", label: "Score", align: "right" },
  { key: "commits", label: "Commits", align: "right" },
  { key: "lines_added", label: "Lines +", align: "right" },
  { key: "lines_deleted", label: "Lines −", align: "right" },
  { key: "prs_merged", label: "PRs", align: "right" },
  { key: "feat_count", label: "Feat", align: "right" },
  { key: "fix_count", label: "Fix", align: "right" },
  { key: "chore_count", label: "Chore", align: "right" },
  { key: "reviews_approved", label: "Rev ✓", align: "right" },
  { key: "reviews_commented", label: "Rev 💬", align: "right" },
  { key: "issues_opened", label: "Opened", align: "right" },
  { key: "issues_closed", label: "Closed", align: "right" },
  { key: "files_edited", label: "Files", align: "right" },
  { key: "files_edited_pct", label: "Files %", align: "right" },
  { key: "directories_touched", label: "Dirs", align: "right" },
  { key: "cross_team_pct", label: "Cross %", align: "right" },
];

function formatCell(key: SortKey, val: string | number): string {
  if (typeof val === "string") return val;
  if (key === "files_edited_pct" || key === "cross_team_pct")
    return `${val.toFixed(1)}%`;
  return val.toLocaleString();
}

export default function EngineerTable({
  engineers,
}: {
  engineers: Engineer[];
}) {
  const [sortKey, setSortKey] = useState<SortKey>("engineer_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const sorted = useMemo(() => {
    return [...engineers].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "string" && typeof bVal === "string")
        return sortDir === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      return sortDir === "asc"
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }, [engineers, sortKey, sortDir]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <section>
      <h2 className="mb-4 text-2xl font-bold text-gray-900">
        All Engineers
      </h2>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-gray-50 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`px-3 py-3 cursor-pointer select-none hover:text-gray-900 transition-colors ${
                    col.align === "right" ? "text-right" : ""
                  }`}
                  onClick={() => handleSort(col.key)}
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="ml-1">
                      {sortDir === "asc" ? "▲" : "▼"}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((eng, i) => (
              <tr
                key={eng.username}
                className={`border-t border-gray-100 ${
                  i % 2 === 0 ? "bg-white" : "bg-gray-50/60"
                } hover:bg-blue-50/40 transition-colors`}
              >
                {COLUMNS.map((col) => (
                  <td
                    key={col.key}
                    className={`px-3 py-2.5 tabular-nums ${
                      col.align === "right" ? "text-right" : ""
                    } ${col.key === "username" ? "font-medium" : ""} ${
                      col.key === "engineer_score" ? "font-bold" : ""
                    }`}
                  >
                    {formatCell(col.key, eng[col.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

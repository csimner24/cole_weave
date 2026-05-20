"use client";

import { useState } from "react";
import type { Engineer } from "@/types/engineer";

const FORMULA_TEXT =
  "Score = (1 + Volume) × (1 + Issues Closed) × (1 + Breadth)";
const EXPLANATION =
  "Volume = commits + lines_added + lines_deleted. Each factor uses (1 + value) so that zero in one dimension reduces but does not eliminate the score.";

function volume(e: Engineer) {
  return e.commits + e.lines_added + e.lines_deleted;
}

export default function Leaderboard({ engineers }: { engineers: Engineer[] }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const top5 = engineers.slice(0, 5);

  return (
    <section>
      <div className="relative mb-6">
        <h2
          className="text-2xl font-bold text-gray-900 cursor-help inline-block"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          Engineer Score — Who Are the Most Impactful Engineers at PostHog?
        </h2>
        {showTooltip && (
          <div className="absolute left-0 top-full mt-2 z-10 w-[480px] rounded-lg border border-gray-200 bg-white p-4 shadow-lg">
            <p className="font-mono text-sm text-gray-800">{FORMULA_TEXT}</p>
            <p className="mt-2 text-sm text-gray-500">{EXPLANATION}</p>
          </div>
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-4 py-3">Rank</th>
              <th className="px-4 py-3">Engineer</th>
              <th className="px-4 py-3 text-right">Score</th>
              <th className="px-4 py-3 text-right">Volume</th>
              <th className="px-4 py-3 text-right">Issues Closed</th>
              <th className="px-4 py-3 text-right">Breadth</th>
            </tr>
          </thead>
          <tbody>
            {top5.map((eng, i) => (
              <tr
                key={eng.username}
                className={i % 2 === 0 ? "bg-white" : "bg-gray-50/60"}
              >
                <td className="px-4 py-3 font-semibold text-gray-400">
                  {i + 1}
                </td>
                <td className="px-4 py-3 font-medium text-gray-900">
                  {eng.username}
                </td>
                <td className="px-4 py-3 text-right font-bold tabular-nums">
                  {eng.engineer_score.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-blue-600">
                  {volume(eng).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-green-600">
                  {eng.issues_closed}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-purple-600">
                  {eng.directories_touched}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

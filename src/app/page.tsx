import { getEngineers, getMeta } from "@/lib/data";
import Leaderboard from "@/components/Leaderboard";
import MethodologyBanner from "@/components/MethodologyBanner";
import MetricBarChart from "@/components/MetricBarChart";
import EngineerTable from "@/components/EngineerTable";

const CHART_CONFIG = [
  {
    title: "Volume",
    formula: "Volume = commits + lines_added + lines_deleted",
    description:
      "Total code output: number of commits plus total lines added and deleted across merged PRs. Balances engineers who make many small changes with those who make fewer large changes.",
    color: "rgb(59, 130, 246)",
    getValue: (e: { commits: number; lines_added: number; lines_deleted: number }) =>
      e.commits + e.lines_added + e.lines_deleted,
  },
  {
    title: "Issues Closed",
    formula: "Issues Closed = count of issues closed by engineer",
    description:
      "Total issues closed by this engineer across all types and priorities. Indicates responsiveness and problem-solving throughput.",
    color: "rgb(34, 197, 94)",
    getValue: (e: { issues_closed: number }) => e.issues_closed,
  },
  {
    title: "Breadth",
    formula: "Breadth = count of distinct top-level directories",
    description:
      "Number of distinct top-level directories this engineer committed to. Higher breadth indicates cross-functional scope and versatility across the codebase.",
    color: "rgb(168, 85, 247)",
    getValue: (e: { directories_touched: number }) => e.directories_touched,
  },
] as const;

export default async function DashboardPage() {
  const [engineers, meta] = await Promise.all([getEngineers(), getMeta()]);

  const chartDataSets = CHART_CONFIG.map((cfg) => ({
    ...cfg,
    data: [...engineers]
      .sort((a, b) => cfg.getValue(b) - cfg.getValue(a))
      .slice(0, 10)
      .map((e) => ({ name: e.username, value: cfg.getValue(e) })),
  }));

  return (
    <main className="mx-auto max-w-[1400px] px-4 py-10 sm:px-6 lg:px-8">
      <header className="mb-10">
        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
          Cole Simner - Weave
        </h1>
        <p className="mt-2 text-lg text-gray-500">
          PostHog Engineer Impact Dashboard &middot; Last{" "}
          {meta.days_back} days &middot; {meta.total_engineers} engineers
        </p>
      </header>

      <div className="space-y-10">
        <Leaderboard engineers={engineers} />

        <MethodologyBanner />

        <section>
          <h2 className="mb-6 text-2xl font-bold text-gray-900">
            Primary Metrics
          </h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {chartDataSets.map((chart) => (
              <MetricBarChart
                key={chart.title}
                title={chart.title}
                formula={chart.formula}
                description={chart.description}
                data={chart.data}
                color={chart.color}
              />
            ))}
          </div>
        </section>

        <EngineerTable engineers={engineers} />

        <footer className="border-t border-gray-200 pt-6 pb-4 text-center text-xs text-gray-400">
          Data collected {new Date(meta.collected_at).toLocaleDateString()} &middot;{" "}
          {meta.total_prs} PRs &middot; {meta.total_commits.toLocaleString()}{" "}
          commits &middot; {meta.total_issues.toLocaleString()} issues
        </footer>
      </div>
    </main>
  );
}

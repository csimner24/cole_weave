"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface ChartEntry {
  name: string;
  value: number;
}

interface Props {
  title: string;
  formula: string;
  description: string;
  data: ChartEntry[];
  color: string;
}

export default function MetricBarChart({
  title,
  formula,
  description,
  data,
  color,
}: Props) {
  const [showInfo, setShowInfo] = useState(false);
  const top10 = data.slice(0, 10);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="relative mb-3">
        <h3
          className="text-base font-semibold text-gray-900 cursor-help inline-block"
          onMouseEnter={() => setShowInfo(true)}
          onMouseLeave={() => setShowInfo(false)}
        >
          {title}
        </h3>
        {showInfo && (
          <div className="absolute left-0 top-full mt-1 z-10 w-80 rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
            <p className="font-mono text-xs text-gray-700">{formula}</p>
            <p className="mt-1.5 text-xs text-gray-500">{description}</p>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={top10}
          layout="vertical"
          margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
        >
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e5e7eb",
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
            {top10.map((entry) => (
              <Cell key={entry.name} fill={color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";

const WAGE_COLORS = {
  1: "#94A3B8", // Slate
  2: "#2DD4BF", // Teal
  3: "#3B82F6", // Blue
  4: "#8B5CF6", // Violet
};

const WAGE_NAMES = {
  1: "Level 1 (Entry)",
  2: "Level 2 (Qualified)",
  3: "Level 3 (Experienced)",
  4: "Level 4 (Expert)",
};

export default function WageLevelChart({ data, highlightLevel }) {
  // Transform data for chart
  const chartData = data.map((item) => ({
    name: WAGE_NAMES[item._id] || `Level ${item._id}`,
    level: item._id,
    avgSalary: Math.round(item.avg_salary),
    minSalary: Math.round(item.min_salary),
    maxSalary: Math.round(item.max_salary),
    count: item.count,
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass rounded-xl p-4 shadow-lg border border-slate-200">
          <p className="font-semibold text-slate-900 mb-2">{data.name}</p>
          <div className="space-y-1 text-sm">
            <p className="flex justify-between gap-4">
              <span className="text-slate-500">Avg Salary:</span>
              <span className="font-mono font-semibold text-teal-600">
                ${data.avgSalary.toLocaleString()}
              </span>
            </p>
            <p className="flex justify-between gap-4">
              <span className="text-slate-500">Min:</span>
              <span className="font-mono text-slate-700">
                ${data.minSalary.toLocaleString()}
              </span>
            </p>
            <p className="flex justify-between gap-4">
              <span className="text-slate-500">Max:</span>
              <span className="font-mono text-slate-700">
                ${data.maxSalary.toLocaleString()}
              </span>
            </p>
            <p className="flex justify-between gap-4 pt-1 border-t border-slate-200">
              <span className="text-slate-500">Positions:</span>
              <span className="font-mono text-slate-700">{data.count}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400">
        No wage data available
      </div>
    );
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: "#64748b", fontSize: 12 }}
            axoidLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(15, 23, 42, 0.05)" }} />
          <Bar dataKey="avgSalary" radius={[8, 8, 0, 0]} maxBarSize={60}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={WAGE_COLORS[entry.level]}
                opacity={highlightLevel && highlightLevel !== entry.level ? 0.3 : 1}
                stroke={highlightLevel === entry.level ? "#0F172A" : "transparent"}
                strokeWidth={highlightLevel === entry.level ? 2 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

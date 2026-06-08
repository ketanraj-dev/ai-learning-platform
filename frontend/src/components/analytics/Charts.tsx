import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, Cell,
} from "recharts";
import type { TrendPoint, TopicStat } from "../../types/index";

const COLORS = ["#3B82F6","#22C55E","#F59E0B","#EF4444","#8B5CF6","#06B6D4"];

const tooltipStyle = {
  backgroundColor: "#1E293B",
  border: "1px solid #334155",
  borderRadius: "8px",
  color: "#E2E8F0",
  fontSize: "12px",
};

// ── Weekly trend line chart ────────────────────────────────────
export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
        <XAxis dataKey="week_label" tick={{ fill: "#64748B", fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fill: "#64748B", fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v}%`, "Accuracy"]} />
        <Line
          type="monotone" dataKey="accuracy"
          stroke="#3B82F6" strokeWidth={2.5}
          dot={{ fill: "#3B82F6", r: 4 }}
          activeDot={{ r: 6, fill: "#60A5FA" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Topic accuracy bar chart ───────────────────────────────────
export function TopicsBarChart({ data }: { data: TopicStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
        <XAxis
          dataKey="display_name"
          tick={{ fill: "#64748B", fontSize: 10 }}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis domain={[0, 100]} tick={{ fill: "#64748B", fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v}%`, "Accuracy"]} />
        <Bar dataKey="accuracy_pct" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.accuracy_pct >= 80 ? "#22C55E" : entry.accuracy_pct >= 50 ? "#3B82F6" : "#EF4444"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Radar chart for topic coverage ────────────────────────────
export function TopicsRadar({ data }: { data: TopicStat[] }) {
  const radarData = data.slice(0, 8).map((t) => ({
    topic: t.display_name.split(" ")[0],
    accuracy: t.accuracy_pct,
  }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={radarData}>
        <PolarGrid stroke="#1E293B" />
        <PolarAngleAxis dataKey="topic" tick={{ fill: "#64748B", fontSize: 10 }} />
        <Radar dataKey="accuracy" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.2} strokeWidth={2} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v}%`, "Accuracy"]} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
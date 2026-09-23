import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function chartTime(value) {
  return new Date(value).toLocaleString([], { day: "2-digit", month: "short", hour: "2-digit" });
}

export default function ForecastChart({ points }) {
  const data = points.map((point) => ({ ...point, label: chartTime(point.forecast_time) }));
  if (!data.length) return <div className="empty-state">Forecast unavailable</div>;

  return (
    <div className="chart-wrap" aria-label="Forecast uncertainty chart">
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={data} margin={{ top: 14, right: 8, left: -18, bottom: 4 }}>
          <defs>
            <linearGradient id="uncertainty" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#63d6a3" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#63d6a3" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#dfe8e2" strokeDasharray="3 6" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#64736a", fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis domain={[0, "auto"]} tick={{ fill: "#64736a", fontSize: 11 }} />
          <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #dce7df" }} />
          <Legend />
          <Area type="monotone" dataKey="p90" name="P90" stroke="none" fill="url(#uncertainty)" />
          <Area type="monotone" dataKey="p10" name="P10" stroke="#94b9a6" fill="#ffffff" fillOpacity={0.72} />
          <Line type="monotone" dataKey="p50" name="P50" stroke="#067a50" strokeWidth={3} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

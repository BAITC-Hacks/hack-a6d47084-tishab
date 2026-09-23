import { useI18n } from "../i18n/LanguageProvider";
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const COLORS = ["#37f5c3", "#ffae57", "#7086ff", "#e365ff", "#35c7e8", "#f8db62"];

export default function ModelComparison({ points }) {
  const { t, number } = useI18n();
  const modelNames = useMemo(
    () => Array.from(new Set(points.flatMap((point) => Object.keys(point.model_predictions || {})))),
    [points],
  );
  const [visible, setVisible] = useState([]);

  useEffect(() => setVisible(modelNames), [modelNames]);

  const data = points.map((point) => ({
    label: `+${point.lead_hours} ${t("h")}`,
    ensemble_p50: point.p50,
    ...point.model_predictions,
  }));

  if (!modelNames.length) return <div className="empty-state">{t("No model predictions supplied")}</div>;

  const toggle = (name) =>
    setVisible((current) => (current.includes(name) ? current.filter((item) => item !== name) : [...current, name]));

  return (
    <div>
      <div className="model-toggles">
        {modelNames.map((name) => (
          <button className={visible.includes(name) ? "model-chip active" : "model-chip"} key={name} onClick={() => toggle(name)}>
            <span style={{ background: COLORS[modelNames.indexOf(name) % COLORS.length] }} />
            {name}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={290}>
        <LineChart data={data} margin={{ left: -18, right: 8, top: 12 }}>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 7" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "var(--chart-label)", fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
          <YAxis tickFormatter={number} tick={{ fill: "var(--chart-label)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip formatter={(value) => number(value)} contentStyle={{ borderRadius: 12, border: "1px solid var(--chart-border)", background: "var(--chart-tooltip)", color: "var(--chart-text)" }} />
          <Legend />
          {modelNames.filter((name) => visible.includes(name)).map((name, index) => (
            <Line key={name} type="monotone" dataKey={name} stroke={COLORS[index % COLORS.length]} dot={false} strokeWidth={2} />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <p className="helper-text">{t("Metrics: N/A until the evaluation module supplies them.")}</p>
    </div>
  );
}

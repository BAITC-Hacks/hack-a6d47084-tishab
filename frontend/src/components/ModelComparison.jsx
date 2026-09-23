import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const COLORS = ["#067a50", "#d66b2c", "#4f67d8", "#9a4bc5", "#177e89", "#a17c00"];

export default function ModelComparison({ points }) {
  const modelNames = useMemo(
    () => Array.from(new Set(points.flatMap((point) => Object.keys(point.model_predictions || {})))),
    [points],
  );
  const [visible, setVisible] = useState([]);

  useEffect(() => setVisible(modelNames), [modelNames]);

  const data = points.map((point) => ({
    label: `+${point.lead_hours}h`,
    ensemble_p50: point.p50,
    ...point.model_predictions,
  }));

  if (!modelNames.length) return <div className="empty-state">No model predictions supplied</div>;

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
          <CartesianGrid stroke="#dfe8e2" strokeDasharray="3 6" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#64736a", fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis tick={{ fill: "#64736a", fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {modelNames.filter((name) => visible.includes(name)).map((name, index) => (
            <Line key={name} type="monotone" dataKey={name} stroke={COLORS[index % COLORS.length]} dot={false} strokeWidth={2} />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <p className="helper-text">Metrics: N/A until the evaluation module supplies them.</p>
    </div>
  );
}

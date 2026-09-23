import { useEffect, useState } from "react";
import { api } from "../services/api";

const metric = (value) => value == null ? "N/A" : value;

export default function Backtest() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { api.latestBacktest().then(setResult).catch((requestError) => setError(requestError.message)); }, []);
  return (
    <section>
      <div className="page-heading"><span className="eyebrow">Evaluation interface</span><h1>Backtest</h1><p>The web layer renders team metrics without calculating or inventing them.</p></div>
      {error && <div className="alert error">Backtest unavailable: {error}</div>}
      {result && <div className="panel table-panel">
        {result.is_mock && <span className="demo-tag">MOCK PLACEHOLDER</span>}
        <p className="helper-text">{result.message}</p>
        <div className="table-scroll"><table><thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>nMAE</th></tr></thead><tbody>
          {result.models.map((model) => <tr key={model.name}><td>{model.name}</td><td>{metric(model.mae)}</td><td>{metric(model.rmse)}</td><td>{metric(model.nmae)}</td></tr>)}
        </tbody></table></div>
        {!result.series.length && <div className="empty-state compact-empty">Actual vs Forecast will appear when the evaluation module supplies a series.</div>}
      </div>}
    </section>
  );
}

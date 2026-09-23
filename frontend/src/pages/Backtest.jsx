import { useI18n } from "../i18n/LanguageProvider";
import { useEffect, useState } from "react";
import { api } from "../services/api";


export default function Backtest() {
  const { t, number, errorText } = useI18n();
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { api.latestBacktest().then(setResult).catch((requestError) => setError(requestError.message)); }, []);
  return (
    <section>
      <div className="page-heading"><span className="eyebrow">{t("Evaluation interface")}</span><h1>{t("Backtest")}</h1><p>{t("The web layer renders team metrics without calculating or inventing them.")}</p></div>
      {error && <div className="alert error">{t("Backtest unavailable:")} {errorText(error)}</div>}
      {result && <div className="panel table-panel">
        {result.is_mock && <span className="demo-tag">{t("MOCK PLACEHOLDER")}</span>}
        <p className="helper-text">{t(result.message)}</p>
        <div className="table-scroll"><table><thead><tr><th>{t("Model")}</th><th>MAE</th><th>RMSE</th><th>nMAE</th></tr></thead><tbody>
          {result.models.map((model) => <tr key={model.name}><td>{model.name}</td><td>{number(model.mae)}</td><td>{number(model.rmse)}</td><td>{number(model.nmae)}</td></tr>)}
        </tbody></table></div>
        {!result.series.length && <div className="empty-state compact-empty">{t("Actual vs Forecast will appear when the evaluation module supplies a series.")}</div>}
      </div>}
    </section>
  );
}

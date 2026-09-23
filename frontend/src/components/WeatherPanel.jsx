import { useI18n } from "../i18n/LanguageProvider";
export default function WeatherPanel({ weather }) {
  const { t, date, number } = useI18n();
  if (!weather) return <div className="empty-state">{t("Weather unavailable")}</div>;
  const sample = weather.hourly?.[0];
  return (
    <article>
      <div className="section-title-row">
        <div><span className="eyebrow">{t("Weather context")}</span><h3>{t(weather.weather_source || "Unknown source")}</h3></div>
        {weather.is_mock && <span className="demo-tag">{t("DEMO DATA")}</span>}
      </div>
      <dl className="detail-list">
        <div><dt>{t("Selected run")}</dt><dd>{weather.weather_run_id || t("N/A")}</dd></div>
        <div><dt>{t("Run time")}</dt><dd>{date(weather.forecast_run_time)}</dd></div>
        <div><dt>{t("Available")}</dt><dd>{date(weather.forecast_available_time)}</dd></div>
        <div><dt>{t("First-hour wind")}</dt><dd>{number(sample?.wind_100m)} {sample?.wind_100m != null && t("m/s @ 100m")}</dd></div>
        <div><dt>{t("Temperature")}</dt><dd>{number(sample?.temperature)}{sample?.temperature != null && "°C"}</dd></div>
        <div><dt>{t("Direction")}</dt><dd>{number(sample?.wind_direction)}{sample?.wind_direction != null && "°"}</dd></div>
      </dl>
    </article>
  );
}

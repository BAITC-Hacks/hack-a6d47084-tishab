export default function WeatherPanel({ weather }) {
  if (!weather) return <div className="empty-state">Weather unavailable</div>;
  const sample = weather.hourly?.[0];
  return (
    <article>
      <div className="section-title-row">
        <div><span className="eyebrow">Weather context</span><h3>{weather.weather_source || "Unknown source"}</h3></div>
        {weather.is_mock && <span className="demo-tag">DEMO DATA</span>}
      </div>
      <dl className="detail-list">
        <div><dt>Selected run</dt><dd>{weather.weather_run_id || "N/A"}</dd></div>
        <div><dt>Run time</dt><dd>{weather.forecast_run_time ? new Date(weather.forecast_run_time).toLocaleString() : "N/A"}</dd></div>
        <div><dt>Available</dt><dd>{weather.forecast_available_time ? new Date(weather.forecast_available_time).toLocaleString() : "N/A"}</dd></div>
        <div><dt>First-hour wind</dt><dd>{sample?.wind_100m ?? "N/A"} {sample?.wind_100m != null && "m/s @ 100m"}</dd></div>
        <div><dt>Temperature</dt><dd>{sample?.temperature ?? "N/A"}{sample?.temperature != null && "°C"}</dd></div>
        <div><dt>Direction</dt><dd>{sample?.wind_direction ?? "N/A"}{sample?.wind_direction != null && "°"}</dd></div>
      </dl>
    </article>
  );
}

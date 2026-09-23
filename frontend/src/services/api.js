const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // Keep the HTTP fallback when the backend did not return JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  health: () => request("/api/health"),
  listForecasts: () => request("/api/forecasts"),
  getForecast: (id) => request(`/api/forecasts/${id}`),
  runForecast: (payload) =>
    request("/api/forecasts/run", { method: "POST", body: JSON.stringify(payload) }),
  getLineage: (id) => request(`/api/forecasts/${id}/lineage`),
  getWeather: (id) => request(`/api/forecasts/${id}/weather`),
  getAgent: (id) => request(`/api/forecasts/${id}/agent`),
  getEvents: (id) => request(`/api/forecasts/${id}/events`),
  latestBacktest: () => request("/api/backtests/latest"),
};

export { API_URL };

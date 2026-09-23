import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";

export function useForecast(forecastId = null) {
  const [forecast, setForecast] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const runs = await api.listForecasts();
      setHistory(runs);
      const selectedId = forecastId || runs[0]?.forecast_id;
      setForecast(selectedId ? await api.getForecast(selectedId) : null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [forecastId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const run = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.runForecast(payload);
      setForecast(result);
      setHistory(await api.listForecasts());
      return result;
    } catch (requestError) {
      setError(requestError.message);
      throw requestError;
    } finally {
      setLoading(false);
    }
  }, []);

  return { forecast, history, loading, error, refresh, run };
}

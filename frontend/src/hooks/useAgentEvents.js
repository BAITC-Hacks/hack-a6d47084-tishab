import { useEffect, useState } from "react";
import { api } from "../services/api";

export function useAgentEvents(forecastId) {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!forecastId) return;
    api.getEvents(forecastId).then(setEvents).catch((requestError) => setError(requestError.message));
  }, [forecastId]);

  return { events, error };
}

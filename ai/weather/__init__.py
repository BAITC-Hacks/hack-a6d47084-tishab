"""Historical weather-forecast vintages with an enforced knowledge boundary."""

from ai.weather.vintage import LeakageError, WeatherRun, assert_legal, legal_runs, select_legal_run

__all__ = ["LeakageError", "WeatherRun", "assert_legal", "legal_runs", "select_legal_run"]

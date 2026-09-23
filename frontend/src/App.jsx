import { languages } from "./i18n/messages";
import { useI18n } from "./i18n/LanguageProvider";
import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import Backtest from "./pages/Backtest";
import Dashboard from "./pages/Dashboard";
import ForecastDetails from "./pages/ForecastDetails";
import History from "./pages/History";
import { api } from "./services/api";

const NavIcon = ({ children }) => <span className="nav-icon" aria-hidden="true">{children}</span>;

const BrandMark = () => (
  <svg className="brand-mark" viewBox="0 0 40 40" aria-hidden="true">
    <circle className="brand-mark-ring" cx="20" cy="20" r="18.5" />
    <g className="brand-mark-rotor">
      <path d="M20 18.5 C23 13.5 23.8 7.5 20.8 4.5 C19.7 3.9 18.9 5.1 19 7.2 L19.4 18.4 Z" />
      <path d="M20 18.5 C23 13.5 23.8 7.5 20.8 4.5 C19.7 3.9 18.9 5.1 19 7.2 L19.4 18.4 Z" transform="rotate(120 20 20)" />
      <path d="M20 18.5 C23 13.5 23.8 7.5 20.8 4.5 C19.7 3.9 18.9 5.1 19 7.2 L19.4 18.4 Z" transform="rotate(240 20 20)" />
      <circle cx="20" cy="20" r="2.5" />
    </g>
  </svg>
);

export default function App() {
  const { t, language, setLanguage } = useI18n();
  const [health, setHealth] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem("windline-theme") || "dark");

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("windline-theme", theme);
  }, [theme]);

  const providerMode = health ? t("API online") : t("Offline");

  return (
    <div className="app-shell">
      <aside className="side-rail">
        <NavLink className="brand" to="/" aria-label={t("Windline home")}>
          <BrandMark />
          <span>Windline<small>{t("Forecast OS")}</small></span>
        </NavLink>
        <nav>
          <NavLink to="/" end><NavIcon>⌁</NavIcon><span>{t("Overview")}</span></NavLink>
          <NavLink to="/history"><NavIcon>◫</NavIcon><span>{t("History")}</span></NavLink>
          <NavLink to="/backtest"><NavIcon>⌁</NavIcon><span>{t("Backtest")}</span></NavLink>
        </nav>
        <div className={`rail-status ${health ? "online" : "offline"}`}>
          <i />
          <div><span>{t("System")}</span><strong>{providerMode}</strong></div>
        </div>
        <div className="rail-signature"><span>VANE</span><small>{t("Vintage-aware energy")}</small></div>
      </aside>
      <div className="app-stage">
        <header className="topbar">
          <div><span className="topbar-kicker">{t("Almaty wind field")}</span><strong>{t("Operations deck")}</strong></div>
          <div className="topbar-actions">
            <span className={`mode-pill ${health ? "online" : "offline"}`}><i /> {providerMode}</span>
            <span className="utc-clock">{t("UTC · Vintage safe")}</span>
            <label className="language-picker">
              <span className="sr-only">{t("Language")}</span>
              <select value={language} onChange={(event) => setLanguage(event.target.value)}>
                {languages.map(({ code, name }) => <option key={code} value={code} lang={code}>{name}</option>)}
              </select>
            </label>
            <button
              className="theme-toggle"
              type="button"
              onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
              aria-label={theme === "dark" ? t("Switch to light theme") : t("Switch to dark theme")}
              title={theme === "dark" ? t("Dark theme") : t("Light theme")}
            >
              <span className="theme-toggle-track"><i className="theme-toggle-thumb">{theme === "dark" ? "☾" : "☀"}</i></span>
              <b>{theme === "dark" ? t("Dark") : t("Light")}</b>
            </button>
          </div>
        </header>
        <main><Routes><Route path="/" element={<Dashboard />} /><Route path="/forecasts/:id" element={<ForecastDetails />} /><Route path="/history" element={<History />} /><Route path="/backtest" element={<Backtest />} /></Routes></main>
        <footer><span>{t("Agentic AI for Vintage-Aware Wind Power Forecasting")}</span><span>{t("Web layer · PoC")}</span></footer>
      </div>
    </div>
  );
}

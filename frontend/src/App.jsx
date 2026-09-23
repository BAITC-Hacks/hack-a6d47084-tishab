import { NavLink, Route, Routes } from "react-router-dom";
import Backtest from "./pages/Backtest";
import Dashboard from "./pages/Dashboard";
import ForecastDetails from "./pages/ForecastDetails";
import History from "./pages/History";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/"><span className="brand-mark">W</span><span>Windline<small>Vintage-aware forecasting</small></span></NavLink>
        <nav><NavLink to="/" end>Dashboard</NavLink><NavLink to="/history">History</NavLink><NavLink to="/backtest">Backtest</NavLink></nav>
        <span className="mode-pill"><i /> Mock providers</span>
      </header>
      <main><Routes><Route path="/" element={<Dashboard />} /><Route path="/forecasts/:id" element={<ForecastDetails />} /><Route path="/history" element={<History />} /><Route path="/backtest" element={<Backtest />} /></Routes></main>
      <footer><span>Agentic AI for Vintage-Aware Wind Power Forecasting</span><span>Web layer · PoC</span></footer>
    </div>
  );
}

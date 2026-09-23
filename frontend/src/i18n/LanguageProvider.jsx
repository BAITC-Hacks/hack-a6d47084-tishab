import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { formatDate, formatNumber, normalizeLanguage, translate } from "./messages";

const I18nContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    try { return normalizeLanguage(localStorage.getItem("windline-language")); }
    catch { return "en"; }
  });

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = `Windline · ${translate(language, "Wind power forecast")}`;
    try { localStorage.setItem("windline-language", language); }
    catch { /* Language switching still works when storage is unavailable. */ }
  }, [language]);

  const value = useMemo(() => ({
    language,
    setLanguage: (next) => setLanguage(normalizeLanguage(next)),
    t: (key, values) => translate(language, key, values),
    date: (value, options) => formatDate(language, value, options),
    number: (value) => formatNumber(language, value),
    errorText: (message) => {
      const match = /^Request failed \((\d+)\)$/.exec(message);
      return match ? translate(language, "Request failed ({status})", { status: match[1] }) : translate(language, message);
    },
  }), [language]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used within LanguageProvider");
  return context;
}


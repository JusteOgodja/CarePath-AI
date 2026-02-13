import React from "react";

export type Language = "fr" | "en";

type I18nContextValue = {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
};

const I18nContext = React.createContext<I18nContextValue | null>(null);

const STORAGE_KEY = "carepath_language";

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = React.useState<Language>(() => {
    if (typeof window === "undefined") return "fr";
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "en" ? "en" : "fr";
  });

  const setLanguage = React.useCallback((lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, lang);
    }
  }, []);

  const toggleLanguage = React.useCallback(() => {
    setLanguage(language === "fr" ? "en" : "fr");
  }, [language, setLanguage]);

  const value = React.useMemo(
    () => ({ language, setLanguage, toggleLanguage }),
    [language, setLanguage, toggleLanguage]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = React.useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return ctx;
}

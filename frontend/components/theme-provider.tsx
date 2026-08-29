"use client";

import * as React from "react";

const ThemeProviderContext = React.createContext<{ theme: "dark" }>({ theme: "dark" });

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  React.useEffect(() => {
    document.documentElement.classList.add("dark");
    document.documentElement.style.colorScheme = "dark";
  }, []);

  return <ThemeProviderContext.Provider value={{ theme: "dark" }}>{children}</ThemeProviderContext.Provider>;
}

export function useTheme() {
  return React.useContext(ThemeProviderContext);
}
import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

function initialTheme(): Theme {
  const saved = localStorage.getItem("phantom-vox-theme") as Theme | null;
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("phantom-vox-theme", theme);
  }, [theme]);
  return { theme, toggle: () => setTheme((value) => (value === "dark" ? "light" : "dark")) };
}

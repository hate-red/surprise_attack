"use client";

import { useEffect, useState } from "react";

export type Theme = "dark" | "light";

const THEME_STORAGE_KEY = "smart-ste-theme";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    if (window.localStorage.getItem(THEME_STORAGE_KEY) === "light") setTheme("light");
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  }

  return { theme, toggleTheme };
}

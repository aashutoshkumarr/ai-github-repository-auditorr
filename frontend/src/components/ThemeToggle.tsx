"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = window.localStorage.getItem("theme");
    const preferred = savedTheme === "light" || savedTheme === "dark" ? savedTheme : "dark";
    setTheme(preferred);
    document.documentElement.dataset.theme = preferred;
  }, []);

  const handleSelectTheme = (newTheme: "dark" | "light") => {
    setTheme(newTheme);
    document.documentElement.dataset.theme = newTheme;
    window.localStorage.setItem("theme", newTheme);
  };

  if (!mounted) {
    return (
      <div className="h-8 w-28 rounded-full bg-slate-900 border border-slate-800 animate-pulse" />
    );
  }

  const isDark = theme === "dark";

  return (
    <div
      role="radiogroup"
      aria-label="Theme selection"
      className={`inline-flex items-center p-1 rounded-full border transition-all duration-200 ${
        isDark
          ? "bg-slate-950/90 border-slate-800 shadow-inner"
          : "bg-slate-200/90 border-slate-300 shadow-inner"
      }`}
    >
      {/* Dark Mode Button */}
      <button
        type="button"
        role="radio"
        aria-checked={isDark}
        onClick={() => handleSelectTheme("dark")}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-all duration-200 ${
          isDark
            ? "bg-slate-800 text-blue-400 border border-blue-500/40 shadow-sm"
            : "text-slate-500 hover:text-slate-800"
        }`}
        title="Switch to Dark Theme"
      >
        <Moon className={`w-3.5 h-3.5 ${isDark ? "text-blue-400" : "text-slate-400"}`} />
        <span className={isDark ? "text-slate-100 font-bold" : "text-slate-500"}>Dark</span>
      </button>

      {/* Light Mode Button */}
      <button
        type="button"
        role="radio"
        aria-checked={!isDark}
        onClick={() => handleSelectTheme("light")}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-all duration-200 ${
          !isDark
            ? "bg-white text-amber-600 border border-amber-400/50 shadow-sm"
            : "text-slate-400 hover:text-slate-200"
        }`}
        title="Switch to Light Theme"
      >
        <Sun className={`w-3.5 h-3.5 ${!isDark ? "text-amber-500" : "text-slate-400"}`} />
        <span className={!isDark ? "text-slate-900 font-bold" : "text-slate-400"}>Light</span>
      </button>
    </div>
  );
}

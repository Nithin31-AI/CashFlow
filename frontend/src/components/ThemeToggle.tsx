"use client";

import React from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "@/lib/theme";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();

  return (
    <div className={`flex items-center p-1 rounded-xl bg-theme-secondary border border-theme-border ${className}`}>
      <button
        onClick={() => setTheme("light")}
        aria-label="Light mode"
        className={`p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
          theme === "light"
            ? "bg-theme-surface text-theme-text shadow-sm"
            : "text-theme-textMuted hover:text-theme-text"
        }`}
        title="Light Cream Mode"
      >
        <Sun className="w-3.5 h-3.5 text-[#788B63]" />
      </button>

      <button
        onClick={() => setTheme("dark")}
        aria-label="Dark mode"
        className={`p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
          theme === "dark"
            ? "bg-theme-surface text-theme-text shadow-sm"
            : "text-theme-textMuted hover:text-theme-text"
        }`}
        title="Dark Charcoal Mode"
      >
        <Moon className="w-3.5 h-3.5 text-[#A3B18A]" />
      </button>

      <button
        onClick={() => setTheme("system")}
        aria-label="System mode"
        className={`p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
          theme === "system"
            ? "bg-theme-surface text-theme-text shadow-sm"
            : "text-theme-textMuted hover:text-theme-text"
        }`}
        title="Follow System Theme"
      >
        <Monitor className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

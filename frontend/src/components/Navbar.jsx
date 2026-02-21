import React from "react";

export default function Navbar({ route, onNavigate, theme, onToggleTheme }) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900">
            AI
          </div>
          <div>
            <div className="text-sm font-semibold leading-4">Smart Incident Triage Agent</div>
            <div className="text-xs text-slate-600 dark:text-slate-300">IT Support Automation</div>
          </div>
        </div>

        <nav className="flex items-center gap-2">
          <button
            onClick={() => onNavigate("submit")}
            className={
              "rounded-lg px-3 py-2 text-sm font-medium " +
              (route === "submit"
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-900")
            }
          >
            Submit Ticket
          </button>
          <button
            onClick={() => onNavigate("dashboard")}
            className={
              "rounded-lg px-3 py-2 text-sm font-medium " +
              (route === "dashboard"
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-900")
            }
          >
            Dashboard
          </button>

          <button
            onClick={onToggleTheme}
            className="ml-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-800"
            title="Toggle dark/light mode"
          >
            Theme: {theme === "dark" ? "Dark" : "Light"}
          </button>
        </nav>
      </div>
    </header>
  );
}

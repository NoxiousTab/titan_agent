import React, { useEffect, useMemo, useState } from "react";
import Navbar from "./components/Navbar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import SubmitTicket from "./pages/SubmitTicket.jsx";

function getInitialTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "dark" || saved === "light") return saved;
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [route, setRoute] = useState("submit");
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  const page = useMemo(() => {
    if (route === "dashboard") return <Dashboard />;
    return <SubmitTicket />;
  }, [route]);

  return (
    <div className="min-h-screen">
      <Navbar
        route={route}
        onNavigate={setRoute}
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
      />
      <main className="mx-auto max-w-6xl px-4 py-6">{page}</main>
    </div>
  );
}

import React from "react";

const styles = {
  P1: "bg-red-600 text-white",
  P2: "bg-orange-500 text-white",
  P3: "bg-yellow-400 text-slate-900",
  P4: "bg-green-600 text-white"
};

export default function SeverityBadge({ severity }) {
  const cls =
    styles[severity] || "bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-slate-100";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}>
      {severity || "N/A"}
    </span>
  );
}

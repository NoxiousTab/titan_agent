import React from "react";

function SeverityPill({ label, value, className }) {
  return (
    <div className={"flex items-center justify-between rounded-lg px-3 py-2 text-sm font-semibold " + className}>
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}

function Card({ title, value, subtitle }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{title}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {subtitle ? <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">{subtitle}</div> : null}
    </div>
  );
}

export default function MetricsCards({ metrics }) {
  const sevMap = Object.fromEntries((metrics.by_severity || []).map((x) => [x.name, x.value]));
  const p1 = sevMap.P1 || 0;
  const p2 = sevMap.P2 || 0;
  const p3 = sevMap.P3 || 0;
  const p4 = sevMap.P4 || 0;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Card title="Total Tickets" value={metrics.total_tickets} subtitle="All submitted incidents & requests" />
      <Card title="Escalated Tickets" value={metrics.escalated_tickets} subtitle="Auto-escalated P1 incidents" />
      <Card title="Monitoring Tickets" value={metrics.monitoring_tickets || 0} subtitle="Generated from Datadog alerts" />
      <Card
        title="Duplicate Tickets Prevented"
        value={metrics.duplicate_tickets_prevented}
        subtitle="Detected via semantic similarity"
      />
      <Card
        title="Estimated Engineer Hours Saved"
        value={metrics.estimated_engineer_hours_saved}
        subtitle="Heuristic based on prevented duplicates"
      />
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Severity</div>
        <div className="mt-3 grid gap-2">
          <SeverityPill label="P1" value={p1} className="bg-red-600 text-white" />
          <SeverityPill label="P2" value={p2} className="bg-orange-500 text-white" />
          <SeverityPill label="P3" value={p3} className="bg-yellow-400 text-slate-900" />
          <SeverityPill label="P4" value={p4} className="bg-green-600 text-white" />
        </div>
        <div className="mt-3 text-xs text-slate-600 dark:text-slate-300">Live counts by priority (P1–P4)</div>
      </div>
    </div>
  );
}

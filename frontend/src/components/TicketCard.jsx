import React from "react";
import SeverityBadge from "./SeverityBadge.jsx";

export default function TicketCard({ ticket }) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-sm font-semibold">{ticket.title}</div>
          <SeverityBadge severity={ticket.severity} />
        </div>
        <div className="mt-2 text-xs text-slate-600 dark:text-slate-300">
          Confidence: <span className="font-semibold">{(ticket.confidence * 100).toFixed(0)}%</span>
          {" · "}
          Assigned team: <span className="font-semibold">{ticket.assigned_team}</span>
          {" · "}
          Status: <span className="font-semibold">{ticket.lifecycle_status || "TRIAGED"}</span>
        </div>

        {ticket.ai_reasoning ? (
          <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              AI Reasoning
            </div>
            <div className="mt-1">{ticket.ai_reasoning}</div>
          </div>
        ) : null}

        {ticket.decision_trace ? (
          <details className="mt-3 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
            <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              AI Decision Trace
            </summary>
            <div className="mt-3 space-y-1 text-sm">
              {ticket.decision_trace.triage_source ? (
                <div>
                  <span className="font-semibold">Triage source:</span> {ticket.decision_trace.triage_source}
                </div>
              ) : null}
              <div>
                <span className="font-semibold">Signals detected:</span>{" "}
                {ticket.decision_trace.signals_detected ? `"${ticket.decision_trace.signals_detected}"` : "N/A"}
              </div>
              <div>
                <span className="font-semibold">Severity logic:</span> {ticket.decision_trace.severity_logic || "N/A"}
              </div>
              <div>
                <span className="font-semibold">Routing logic:</span> {ticket.decision_trace.routing_logic || "N/A"}
              </div>
              <div>
                <span className="font-semibold">Duplicate score:</span> {Number(ticket.decision_trace.duplicate_score || 0).toFixed(2)}
              </div>
              <div>
                <span className="font-semibold">Escalation triggered:</span>{" "}
                {ticket.decision_trace.escalation_triggered ? "Yes" : "No"}
              </div>
            </div>
          </details>
        ) : null}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="text-sm font-semibold">Suggested First-Level Fixes</div>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-200">
          {(ticket.suggested_fixes || []).map((s, idx) => (
            <li key={idx}>{s}</li>
          ))}
        </ol>
      </div>

      {ticket.is_duplicate ? (
        <div className="rounded-xl border border-yellow-300 bg-yellow-50 p-4 text-sm text-yellow-900 dark:border-yellow-900/40 dark:bg-yellow-950/30 dark:text-yellow-100">
          Duplicate detected. Similar to ticket #{ticket.duplicate_ticket_id} (similarity {(ticket.similarity_score || 0).toFixed(2)}).
        </div>
      ) : null}

      {ticket.escalated ? (
        <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-900 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-100">
          Escalated automatically (P1). Jira issue: <span className="font-semibold">{ticket.jira_issue_key || "N/A"}</span>. n8n workflow triggered if configured.
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
          Not escalated. Escalation triggers only for P1 incidents.
        </div>
      )}
    </div>
  );
}

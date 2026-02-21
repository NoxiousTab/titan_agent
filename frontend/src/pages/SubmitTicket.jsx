import React, { useState } from "react";
import TicketForm from "../components/TicketForm.jsx";
import TicketCard from "../components/TicketCard.jsx";
import { createTicket } from "../services/api.js";

export default function SubmitTicket() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function onSubmit(form) {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await createTicket(form);
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to submit ticket. Is backend running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h1 className="text-xl font-semibold">Submit Ticket</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          AI will classify severity, route the ticket, suggest fixes, detect duplicates, and escalate P1 incidents.
        </p>

        <div className="mt-5">
          <TicketForm onSubmit={onSubmit} loading={loading} />
        </div>

        {error ? (
          <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-200">
            {error}
          </div>
        ) : null}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold">Triage Result</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Enterprise triage output: severity, confidence, routing, duplicate analysis, and escalation automation.
        </p>

        <div className="mt-5">
          {loading ? (
            <div className="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900 dark:border-slate-700 dark:border-t-slate-100"></div>
              Processing with AI engine...
            </div>
          ) : result ? (
            <TicketCard ticket={result} />
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300">
              Submit a ticket to see triage output here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

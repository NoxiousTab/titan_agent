import React, { useState } from "react";

export default function TicketForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    reporter: "",
    department: ""
  });

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
      className="space-y-4"
    >
      <div>
        <label className="text-sm font-medium">Title</label>
        <input
          value={form.title}
          onChange={(e) => update("title", e.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-900/20 dark:border-slate-800 dark:bg-slate-950 dark:focus:ring-slate-100/20"
          placeholder="e.g., VPN not connecting for multiple users"
          required
          minLength={3}
        />
      </div>

      <div>
        <label className="text-sm font-medium">Description</label>
        <textarea
          value={form.description}
          onChange={(e) => update("description", e.target.value)}
          className="mt-1 min-h-[120px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-900/20 dark:border-slate-800 dark:bg-slate-950 dark:focus:ring-slate-100/20"
          placeholder="Add impact, scope, errors, and when it started."
          required
          minLength={10}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-sm font-medium">Reporter</label>
          <input
            value={form.reporter}
            onChange={(e) => update("reporter", e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-900/20 dark:border-slate-800 dark:bg-slate-950 dark:focus:ring-slate-100/20"
            placeholder="e.g., Jane Doe"
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium">Department</label>
          <input
            value={form.department}
            onChange={(e) => update("department", e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-900/20 dark:border-slate-800 dark:bg-slate-950 dark:focus:ring-slate-100/20"
            placeholder="e.g., Finance"
            required
          />
        </div>
      </div>

      <button
        disabled={loading}
        className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        type="submit"
      >
        {loading ? "Submitting..." : "Submit Ticket"}
      </button>
    </form>
  );
}

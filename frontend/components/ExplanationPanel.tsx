"use client";

import { useState } from "react";
import type { ExplanationDoc } from "@/lib/types";

/**
 * Collapsible explanation panel (WP-07 task 5) rendering an ExplanationDoc:
 * purpose, configuration list, signals table, reset/enable behavior,
 * assumptions, limitations.
 */
export function ExplanationPanel({ doc }: { doc: ExplanationDoc | null }) {
  const [open, setOpen] = useState(true);

  if (!doc) return null;

  return (
    <section className="rounded border border-zinc-200 dark:border-zinc-800">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-3 py-2 text-sm font-semibold text-zinc-800 dark:text-zinc-200"
      >
        Explanation
        <span aria-hidden>{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <div className="flex flex-col gap-3 border-t border-zinc-200 px-3 py-3 text-xs text-zinc-700 dark:border-zinc-800 dark:text-zinc-300">
          <div>
            <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Purpose</h3>
            <p>{doc.purpose}</p>
          </div>

          {doc.configuration.length > 0 ? (
            <div>
              <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Configuration</h3>
              <ul className="list-disc pl-5">
                {doc.configuration.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {doc.signals.length > 0 ? (
            <div>
              <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Signals</h3>
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-zinc-200 dark:border-zinc-800">
                    <th className="py-1 pr-2 font-medium">Name</th>
                    <th className="py-1 pr-2 font-medium">Direction</th>
                    <th className="py-1 font-medium">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {doc.signals.map((s, i) => (
                    <tr key={i} className="border-b border-zinc-100 dark:border-zinc-900">
                      <td className="py-1 pr-2 font-mono">{s.name}</td>
                      <td className="py-1 pr-2">{s.direction}</td>
                      <td className="py-1">{s.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          <div>
            <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Reset behavior</h3>
            <p>{doc.reset_behavior}</p>
          </div>

          {doc.enable_behavior ? (
            <div>
              <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Enable behavior</h3>
              <p>{doc.enable_behavior}</p>
            </div>
          ) : null}

          {doc.assumptions.length > 0 ? (
            <div>
              <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Assumptions</h3>
              <ul className="list-disc pl-5">
                {doc.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {doc.limitations.length > 0 ? (
            <div>
              <h3 className="mb-1 font-semibold text-zinc-900 dark:text-zinc-100">Limitations</h3>
              <ul className="list-disc pl-5">
                {doc.limitations.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

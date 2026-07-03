"use client";

import { useState } from "react";
import type { LintReport } from "@/lib/types";

/**
 * Lint badge (WP-07 task 4):
 *   clean       -> green "Lint clean · verilator -Wall"
 *   warnings    -> amber, expandable message list
 *   unavailable -> grey
 */
export function LintBadge({ lint }: { lint: LintReport | null }) {
  const [open, setOpen] = useState(false);

  if (!lint) {
    return (
      <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium text-zinc-400">
        Lint —
      </span>
    );
  }

  if (lint.status === "clean") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/40 dark:text-green-300">
        <span aria-hidden>●</span> Lint clean · verilator -Wall
      </span>
    );
  }

  if (lint.status === "unavailable") {
    return (
      <span
        className="inline-flex items-center gap-1 rounded bg-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
        title="Verilator not available in this environment."
      >
        <span aria-hidden>○</span> Lint unavailable
      </span>
    );
  }

  // warnings
  return (
    <div className="inline-flex flex-col">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 hover:bg-amber-200 dark:bg-amber-900/40 dark:text-amber-300"
      >
        <span aria-hidden>▲</span> {lint.messages.length} lint warning
        {lint.messages.length === 1 ? "" : "s"}
        <span aria-hidden>{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <ul className="mt-1 flex flex-col gap-1 rounded border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          {lint.messages.map((m, i) => (
            <li key={i}>
              <span className="font-mono font-semibold">
                {m.severity} {m.code}
              </span>
              {m.line ? <span className="opacity-70"> (line {m.line})</span> : null}: {m.text}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

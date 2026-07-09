"use client";

import { useState } from "react";
import type { LintFileReport, LintMessage, LintReport, LintStatus } from "@/lib/types";

/**
 * Lint badge (WP-07 task 4, extended for API v2 in P2-05b):
 *   clean       -> green "Lint clean · verilator -Wall"
 *   warnings    -> amber, expandable message list
 *   unavailable -> grey
 *
 * Accepts either the v1 single LintReport or the v2 list of per-file reports.
 * For the list shape the badge aggregates to the worst status across rtl files
 * and, when expanded, groups messages by file path.
 */

/** One display group: optional file path + its messages. */
interface LintGroup {
  path?: string;
  messages: LintMessage[];
}

type LintInput = LintReport | LintFileReport[] | null;

const RANK: Record<LintStatus, number> = { clean: 0, unavailable: 1, warnings: 2 };

/** Normalise either shape into an aggregate status + grouped messages. */
function aggregate(lint: LintInput): {
  status: LintStatus;
  groups: LintGroup[];
  count: number;
} | null {
  if (!lint) return null;

  const reports: LintFileReport[] = Array.isArray(lint)
    ? lint
    : [{ path: "", ...lint }];
  if (reports.length === 0) return null;

  let status: LintStatus = "clean";
  const groups: LintGroup[] = [];
  let count = 0;
  for (const r of reports) {
    if (RANK[r.status] > RANK[status]) status = r.status;
    if (r.messages.length > 0) {
      groups.push({ path: r.path || undefined, messages: r.messages });
      count += r.messages.length;
    }
  }
  return { status, groups, count };
}

export function LintBadge({ lint }: { lint: LintInput }) {
  const [open, setOpen] = useState(false);
  const agg = aggregate(lint);

  if (!agg) {
    return (
      <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium text-zinc-400">
        Lint —
      </span>
    );
  }

  if (agg.status === "clean") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/40 dark:text-green-300">
        <span aria-hidden>●</span> Lint clean · verilator -Wall
      </span>
    );
  }

  if (agg.status === "unavailable") {
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
        <span aria-hidden>▲</span> {agg.count} lint warning
        {agg.count === 1 ? "" : "s"}
        <span aria-hidden>{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <div className="mt-1 flex flex-col gap-2 rounded border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          {agg.groups.map((g, gi) => (
            <div key={g.path ?? gi} className="flex flex-col gap-1">
              {g.path ? (
                <div className="font-mono text-[11px] font-semibold opacity-80">
                  {g.path}
                </div>
              ) : null}
              <ul className="flex flex-col gap-1">
                {g.messages.map((m, i) => (
                  <li key={i}>
                    <span className="font-mono font-semibold">
                      {m.severity} {m.code}
                    </span>
                    {m.line ? <span className="opacity-70"> (line {m.line})</span> : null}: {m.text}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

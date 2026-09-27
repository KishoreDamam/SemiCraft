"use client";

import { useState } from "react";
import type { LintFileReport, LintMessage, LintReport, LintStatus } from "@/lib/types";

/**
 * Lint badge (WP-07 task 4, extended for API v2 in P2-05b):
 *   clean       -> green lamp, "Lint clean · verilator -Wall"
 *   warnings    -> amber lamp, expandable message list
 *   unavailable -> hollow grey lamp
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

/** Status lamp: a small square, solid when there is a result, hollow when not. */
export function Lamp({ tone }: { tone: "ok" | "warn" | "err" | "off" }) {
  const cls = {
    ok: "bg-ok",
    warn: "bg-warn",
    err: "bg-err",
    off: "border border-ink-3",
  }[tone];
  return <span aria-hidden className={`inline-block h-2 w-2 shrink-0 rounded-[1px] ${cls}`} />;
}

const STATUS_TEXT = "inline-flex items-center gap-2 font-mono text-xs";

export function LintBadge({ lint }: { lint: LintInput }) {
  const [open, setOpen] = useState(false);
  const agg = aggregate(lint);

  if (!agg) {
    return (
      <span className={`${STATUS_TEXT} text-ink-3`}>
        <Lamp tone="off" /> Lint pending
      </span>
    );
  }

  if (agg.status === "clean") {
    return (
      <span className={`${STATUS_TEXT} text-ok`}>
        <Lamp tone="ok" /> Lint clean · verilator -Wall
      </span>
    );
  }

  if (agg.status === "unavailable") {
    return (
      <span
        className={`${STATUS_TEXT} text-ink-3`}
        title="Verilator is not installed where the API runs. Use the Docker image for real lint results."
      >
        <Lamp tone="off" /> Lint unavailable
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
        className={`${STATUS_TEXT} rounded-sm text-warn hover:underline`}
      >
        <Lamp tone="warn" /> {agg.count} lint warning
        {agg.count === 1 ? "" : "s"}
        <span aria-hidden>{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <div className="mt-2 flex flex-col gap-2 border-t border-rule pt-2 text-xs text-ink">
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

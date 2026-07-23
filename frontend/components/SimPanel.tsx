"use client";

import type { SimStatus, SimulateResponse } from "@/lib/types";

/**
 * Smoke-sim log viewer (P3-03): a status badge plus the compile/run stdout and
 * stderr tails returned by POST /api/v2/simulate. Renders nothing until the
 * user has run a sim at least once for the current item.
 *
 * Status → badge mapping mirrors LintBadge's visual language:
 *   pass        -> green
 *   fail/error  -> red
 *   unavailable -> grey (no verilator in this environment)
 *   no_tb       -> grey (item has no testbench)
 */

const BADGE: Record<SimStatus, { className: string; label: string; title?: string }> = {
  pass: {
    className: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
    label: "Sim pass · SMOKE PASS",
  },
  fail: {
    className: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
    label: "Sim fail",
  },
  error: {
    className: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
    label: "Sim error",
    title: "Compile error or timeout — see the log below.",
  },
  unavailable: {
    className: "bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
    label: "Sim unavailable",
    title: "Verilator not available in this environment.",
  },
  no_tb: {
    className: "bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
    label: "No testbench",
    title: "This item generates no smoke testbench.",
  },
};

function LogBlock({ title, text }: { title: string; text: string }) {
  if (!text) return null;
  return (
    <div className="flex flex-col gap-1">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
        {title}
      </div>
      <pre className="max-h-48 overflow-auto rounded bg-zinc-950 p-2 font-mono text-[11px] leading-relaxed text-zinc-200">
        {text}
      </pre>
    </div>
  );
}

export function SimPanel({ result }: { result: SimulateResponse | null }) {
  if (!result) return null;

  const badge = BADGE[result.status];
  const hasLogs = Boolean(result.stdout_tail || result.stderr_tail);

  return (
    <section aria-label="Smoke sim result" className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${badge.className}`}
          title={badge.title}
        >
          <span aria-hidden>●</span> {badge.label}
        </span>
        {result.exit_code !== null ? (
          <span className="text-[11px] text-zinc-400">exit {result.exit_code}</span>
        ) : null}
        <span className="text-[11px] text-zinc-400">
          {result.duration_s.toFixed(2)}s
        </span>
      </div>
      {hasLogs ? (
        <div className="flex flex-col gap-2">
          <LogBlock title="stdout" text={result.stdout_tail} />
          <LogBlock title="stderr" text={result.stderr_tail} />
        </div>
      ) : null}
    </section>
  );
}

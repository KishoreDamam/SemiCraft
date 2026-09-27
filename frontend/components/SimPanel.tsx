"use client";

import type { SimStatus, SimulateResponse } from "@/lib/types";
import { Lamp } from "@/components/LintBadge";

/**
 * Smoke-sim log viewer (P3-03): a status badge plus the compile/run stdout and
 * stderr tails returned by POST /api/v2/simulate. Renders nothing until the
 * user has run a sim at least once for the current item.
 *
 * Status -> lamp mapping mirrors LintBadge's visual language:
 *   pass        -> green
 *   fail/error  -> red
 *   unavailable -> grey (no verilator in this environment)
 *   no_tb       -> grey (item has no testbench)
 */

const BADGE: Record<
  SimStatus,
  { tone: "ok" | "err" | "off"; text: string; label: string; title?: string }
> = {
  pass: { tone: "ok", text: "text-ok", label: "Sim pass · SMOKE PASS" },
  fail: { tone: "err", text: "text-err", label: "Sim fail" },
  error: {
    tone: "err",
    text: "text-err",
    label: "Sim error",
    title: "Compile error or timeout. The log below has the details.",
  },
  unavailable: {
    tone: "off",
    text: "text-ink-3",
    label: "Sim unavailable",
    title: "Verilator is not installed where the API runs.",
  },
  no_tb: {
    tone: "off",
    text: "text-ink-3",
    label: "No testbench",
    title: "This item generates no smoke testbench.",
  },
};

function LogBlock({ title, text }: { title: string; text: string }) {
  if (!text) return null;
  return (
    <div className="flex flex-col gap-1">
      <div className="label-caps">{title}</div>
      <pre className="max-h-48 overflow-auto rounded-sm bg-code-bg p-3 font-mono text-xs leading-relaxed text-code-ink">
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
    <section aria-label="Smoke sim result" className="flex flex-col gap-3 border-t border-rule pt-3">
      <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
        <span className={`inline-flex items-center gap-2 ${badge.text}`} title={badge.title}>
          <Lamp tone={badge.tone} /> {badge.label}
        </span>
        {result.exit_code !== null ? (
          <span className="text-ink-3">exit {result.exit_code}</span>
        ) : null}
        <span className="text-ink-3">
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

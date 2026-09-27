"use client";

import { useState } from "react";
import type { ExplanationDoc } from "@/lib/types";

/**
 * Collapsible explanation, set like a datasheet: section names in the left
 * margin, content beside them, hairlines between. Renders an ExplanationDoc:
 * purpose, configuration, signals, reset/enable behavior, assumptions,
 * limitations.
 */

function Row({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1 border-t border-rule py-4 md:grid-cols-[168px_minmax(0,1fr)] md:gap-6">
      <h3 className="label-caps pt-0.5">{title}</h3>
      <div className="min-w-0 text-sm leading-relaxed text-ink">{children}</div>
    </div>
  );
}

function List({ items }: { items: string[] }) {
  return (
    <ul className="flex flex-col gap-1">
      {items.map((x, i) => (
        <li key={i} className="grid grid-cols-[12px_minmax(0,1fr)] gap-2">
          <span aria-hidden className="mt-[9px] h-px w-2 bg-ink-3" />
          <span>{x}</span>
        </li>
      ))}
    </ul>
  );
}

export function ExplanationPanel({ doc }: { doc: ExplanationDoc | null }) {
  const [open, setOpen] = useState(true);

  if (!doc) return null;

  return (
    <section aria-label="Explanation">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="group flex w-full items-baseline gap-3 py-2 text-left"
      >
        <span className="text-lg font-semibold tracking-[-0.01em] text-ink">Explanation</span>
        <span className="font-mono text-xs text-ink-3 group-hover:text-ink">
          {open ? "hide" : "show"}
        </span>
      </button>
      {open ? (
        <div className="mt-2">
          <Row title="Purpose">
            <p className="max-w-[72ch]">{doc.purpose}</p>
          </Row>

          {doc.configuration.length > 0 ? (
            <Row title="Configuration">
              <List items={doc.configuration} />
            </Row>
          ) : null}

          {doc.signals.length > 0 ? (
            <Row title="Signals">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-sm">
                  <thead>
                    <tr className="border-b border-rule-strong">
                      <th className="label-caps py-1.5 pr-4 font-medium">Name</th>
                      <th className="label-caps py-1.5 pr-4 font-medium">Direction</th>
                      <th className="label-caps py-1.5 font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doc.signals.map((s, i) => (
                      <tr key={i} className="border-b border-rule align-top">
                        <td className="whitespace-nowrap py-1.5 pr-4 font-mono text-[13px]">
                          {s.name}
                        </td>
                        <td className="py-1.5 pr-4 font-mono text-[13px] text-ink-2">
                          {s.direction}
                        </td>
                        <td className="py-1.5 text-ink-2">{s.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Row>
          ) : null}

          <Row title="Reset behavior">
            <p className="max-w-[72ch]">{doc.reset_behavior}</p>
          </Row>

          {doc.enable_behavior ? (
            <Row title="Enable behavior">
              <p className="max-w-[72ch]">{doc.enable_behavior}</p>
            </Row>
          ) : null}

          {doc.assumptions.length > 0 ? (
            <Row title="Assumptions">
              <List items={doc.assumptions} />
            </Row>
          ) : null}

          {doc.limitations.length > 0 ? (
            <Row title="Limitations">
              <List items={doc.limitations} />
            </Row>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

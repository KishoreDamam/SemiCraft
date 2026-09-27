"use client";

import { useEffect, useRef, useState } from "react";
import type { CatalogItem, ItemKind } from "@/lib/types";

const GROUPS: { kind: ItemKind; label: string }[] = [
  { kind: "snippet", label: "Snippets" },
  { kind: "module", label: "Modules" },
  { kind: "ip", label: "IP Blocks" },
];

function matches(item: CatalogItem, query: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  return (
    item.name.toLowerCase().includes(q) ||
    item.id.toLowerCase().includes(q) ||
    item.description.toLowerCase().includes(q)
  );
}

/**
 * Left-panel catalog picker. Groups items into Snippets / Modules / IP Blocks
 * sections and shows a "beta" badge for non-stable maturity. Each item keeps
 * role="option" so it behaves like a single-select listbox.
 *
 * Rows are one line (the description is the row's tooltip; the selected
 * item's description is shown in full by the caller) and the list scrolls
 * inside a bounded box, so the options form below it stays on the first
 * screen however large the catalog grows. A filter box searches name, id and
 * description.
 *
 * An empty group renders nothing, so listing a kind before any item of that
 * kind exists is free — and is what keeps a new backend kind from being
 * silently dropped here.
 */
export function CatalogPicker({
  items,
  selectedId,
  onSelect,
}: {
  items: CatalogItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const listRef = useRef<HTMLDivElement>(null);
  const visible = items.filter((i) => matches(i, query));

  // Keep the selected row in view (e.g. when a permalink selects an IP far
  // down the list). scrollIntoView is absent in jsdom, hence the guard.
  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>('[aria-selected="true"]');
    el?.scrollIntoView?.({ block: "nearest" });
  }, [selectedId]);

  return (
    <div className="flex flex-col gap-2">
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={`Filter ${items.length} generators`}
        aria-label="Filter catalog"
        className="h-8 w-full rounded-sm border border-rule-strong bg-sheet px-2 text-[13px] text-ink placeholder:text-ink-3 hover:border-ink-3"
      />
      <div
        ref={listRef}
        role="listbox"
        aria-label="Catalog"
        className="-mx-1 flex max-h-[34vh] flex-col gap-3 overflow-y-auto px-1 py-1"
      >
        {GROUPS.map(({ kind, label }) => {
          const group = visible.filter((i) => i.kind === kind);
          if (group.length === 0) return null;
          return (
            <div key={kind} className="flex flex-col">
              <h3 className="flex items-baseline justify-between px-2 pb-1">
                <span className="label-caps">{label}</span>
                <span className="font-mono text-[11px] text-ink-3">{group.length}</span>
              </h3>
              {group.map((item) => {
                const active = item.id === selectedId;
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="option"
                    aria-selected={active}
                    title={item.description}
                    onClick={() => onSelect(item.id)}
                    className={`flex h-8 shrink-0 items-center gap-2 rounded-sm px-2 text-left text-sm ${
                      active ? "bg-ink font-medium text-paper" : "text-ink hover:bg-well"
                    }`}
                  >
                    <span className="truncate">{item.name}</span>
                    {item.maturity === "beta" ? (
                      <span
                        className={`ml-auto shrink-0 font-mono text-[11px] ${
                          active ? "text-paper/80" : "text-warn"
                        }`}
                      >
                        beta
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          );
        })}
        {visible.length === 0 ? (
          <p className="px-2 py-1 text-sm text-ink-3">No items match “{query}”.</p>
        ) : null}
      </div>
    </div>
  );
}

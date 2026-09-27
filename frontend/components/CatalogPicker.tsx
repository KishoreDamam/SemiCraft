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
        placeholder={`Filter ${items.length} items…`}
        aria-label="Filter catalog"
        className="w-full rounded border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-800 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
      />
      <div
        ref={listRef}
        role="listbox"
        aria-label="Catalog"
        className="flex max-h-[38vh] flex-col gap-2 overflow-y-auto rounded border border-zinc-200 p-1 dark:border-zinc-800"
      >
        {GROUPS.map(({ kind, label }) => {
          const group = visible.filter((i) => i.kind === kind);
          if (group.length === 0) return null;
          return (
            <div key={kind} className="flex flex-col">
              <h3 className="px-2 pb-0.5 pt-1 text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
                {label}
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
                    className={`flex items-center gap-2 rounded px-2 py-1 text-left text-sm transition-colors ${
                      active
                        ? "bg-blue-600 font-medium text-white"
                        : "text-zinc-800 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-900"
                    }`}
                  >
                    <span className="truncate">{item.name}</span>
                    {item.maturity === "beta" ? (
                      <span
                        className={`ml-auto shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                          active
                            ? "bg-white/20 text-white"
                            : "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300"
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
          <p className="px-2 py-1 text-xs text-zinc-500">No items match “{query}”.</p>
        ) : null}
      </div>
    </div>
  );
}

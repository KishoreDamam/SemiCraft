"use client";

import type { CatalogItem, ItemKind } from "@/lib/types";

const GROUPS: { kind: ItemKind; label: string }[] = [
  { kind: "snippet", label: "Snippets" },
  { kind: "module", label: "Modules" },
];

/**
 * Left-panel catalog picker (P2-05b). Groups items into Snippets / Modules
 * sections and shows a "beta" badge for non-stable maturity. Each item keeps
 * role="option" so it behaves like a single-select listbox.
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
  return (
    <div role="listbox" aria-label="Catalog" className="flex flex-col gap-3">
      {GROUPS.map(({ kind, label }) => {
        const group = items.filter((i) => i.kind === kind);
        if (group.length === 0) return null;
        return (
          <div key={kind} className="flex flex-col gap-1">
            <h3 className="px-1 text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
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
                  onClick={() => onSelect(item.id)}
                  className={`rounded border px-3 py-2 text-left transition-colors ${
                    active
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                      : "border-transparent hover:bg-zinc-100 dark:hover:bg-zinc-900"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                      {item.name}
                    </span>
                    {item.maturity === "beta" ? (
                      <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
                        beta
                      </span>
                    ) : null}
                  </div>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400">
                    {item.description}
                  </div>
                </button>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

"use client";

import type { SnippetCatalogEntry } from "@/lib/types";

/** Left-panel snippet picker (WP-07 task 1). */
export function SnippetPicker({
  snippets,
  selectedId,
  onSelect,
}: {
  snippets: SnippetCatalogEntry[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1" role="listbox" aria-label="Snippet category">
      {snippets.map((s) => {
        const active = s.id === selectedId;
        return (
          <button
            key={s.id}
            type="button"
            role="option"
            aria-selected={active}
            onClick={() => onSelect(s.id)}
            className={`rounded border px-3 py-2 text-left transition-colors ${
              active
                ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                : "border-transparent hover:bg-zinc-100 dark:hover:bg-zinc-900"
            }`}
          >
            <div className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{s.name}</div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">{s.description}</div>
          </button>
        );
      })}
    </div>
  );
}

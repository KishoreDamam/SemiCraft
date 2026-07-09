"use client";

import type { FileKind, GeneratedFile } from "@/lib/types";

/** Dot colour per file kind (rtl / doc / tb). */
const KIND_DOT: Record<FileKind, string> = {
  rtl: "bg-blue-500",
  doc: "bg-emerald-500",
  tb: "bg-amber-500",
};

/**
 * Tab bar shown above the code preview when a generation returns more than one
 * file. Single-file results render nothing (the caller shows the lone file with
 * no tab chrome — identical to the pre-v2 experience).
 */
export function FileTabs({
  files,
  activeIndex,
  onSelect,
}: {
  files: GeneratedFile[];
  activeIndex: number;
  onSelect: (index: number) => void;
}) {
  if (files.length <= 1) return null;

  return (
    <div
      role="tablist"
      aria-label="Generated files"
      className="flex flex-wrap gap-1 border-b border-zinc-200 pb-1 dark:border-zinc-800"
    >
      {files.map((f, i) => {
        const active = i === activeIndex;
        return (
          <button
            key={f.path}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onSelect(i)}
            className={`inline-flex items-center gap-1.5 rounded-t px-3 py-1 text-xs font-medium transition-colors ${
              active
                ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                : "text-zinc-500 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-900"
            }`}
          >
            <span
              aria-hidden
              className={`h-2 w-2 rounded-full ${KIND_DOT[f.kind]}`}
            />
            {f.path}
          </button>
        );
      })}
    </div>
  );
}

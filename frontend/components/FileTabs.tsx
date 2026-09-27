"use client";

import type { FileKind, GeneratedFile } from "@/lib/types";

/** Short kind tag shown before each file name. */
const KIND_TAG: Record<FileKind, string> = {
  rtl: "RTL",
  doc: "DOC",
  tb: "TB",
};

/**
 * Tab bar for multi-file results, drawn inside the code window's title strip.
 * Single-file results render nothing (the caller shows the lone file's name).
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
      className="flex min-w-0 flex-1 gap-0.5 overflow-x-auto"
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
            className={`relative inline-flex h-10 shrink-0 items-center gap-2 px-3 font-mono text-xs ${
              active
                ? "text-code-ink after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:bg-accent"
                : "text-code-ink-3 hover:text-code-ink"
            }`}
          >
            <span className="text-[10px] tracking-wider text-code-ink-3">{KIND_TAG[f.kind]}</span>
            {f.path}
          </button>
        );
      })}
    </div>
  );
}

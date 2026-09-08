"use client";

import { isMockMode } from "@/lib/api";

/**
 * Says out loud that the app is serving built-in demo data (launch blocker B3).
 *
 * `NEXT_PUBLIC_API_BASE` unset means every call is answered by `mocks/` — a
 * hand-written sample of a handful of items, with fabricated output. Through
 * v0.4.0 nothing anywhere in the UI said so, so a deployment that forgot one
 * environment variable served a convincing fake of a much smaller product with
 * no error, no badge and no clue: the catalog looked short, the "IP Blocks"
 * group looked empty, and everything appeared to be working.
 *
 * Deliberately **not dismissible**. A dismissible banner is a banner that is
 * dismissed once and never seen again, which returns the app to exactly the
 * silent state this exists to end.
 */
export function MockBanner() {
  if (!isMockMode()) return null;

  return (
    <div
      role="status"
      data-testid="mock-banner"
      className="flex flex-wrap items-baseline gap-x-2 gap-y-1 border-b border-amber-300 bg-amber-100 px-4 py-2 text-xs text-amber-950 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
    >
      <strong className="font-semibold">Demo data — no backend connected.</strong>
      <span>
        You are seeing a small built-in sample with fabricated output, not the
        real catalog and not real generated RTL.
      </span>
      <span className="opacity-80">
        Set <code className="font-mono">NEXT_PUBLIC_API_BASE</code> to point at a
        SemiCraft backend.
      </span>
    </div>
  );
}

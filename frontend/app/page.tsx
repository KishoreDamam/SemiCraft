"use client";

import { useEffect, useState } from "react";
import type { CatalogV2Response } from "@/lib/types";
import { getCatalog } from "@/lib/api";
import { GeneratorApp, useInitialPermalink } from "@/components/GeneratorApp";
import { Mark } from "@/components/Mark";

function catalogSummary(c: CatalogV2Response): string {
  const n = (kind: string) => c.items.filter((i) => i.kind === kind).length;
  const parts: [number, string, string][] = [
    [n("snippet"), "snippet", "snippets"],
    [n("module"), "module", "modules"],
    [n("ip"), "IP block", "IP blocks"],
  ];
  return parts
    .filter(([count]) => count > 0)
    .map(([count, one, many]) => `${count} ${count === 1 ? one : many}`)
    .join(" · ");
}

/** Placeholder in the shape of the loaded page, so nothing jumps on arrival. */
function LoadingSkeleton() {
  const bar = "rounded-sm bg-well";
  return (
    <div
      aria-busy="true"
      className="grid grid-cols-1 lg:h-full lg:grid-cols-[320px_minmax(0,1fr)]"
    >
      <span className="sr-only" role="status">
        Loading catalog
      </span>
      <div aria-hidden className="flex flex-col gap-2 px-4 py-5 lg:px-5">
        <div className={`${bar} h-3 w-16`} />
        <div className={`${bar} mt-1 h-8`} />
        {[72, 58, 80, 64, 70, 52].map((w, i) => (
          <div key={i} className={`${bar} h-4`} style={{ width: `${w}%` }} />
        ))}
      </div>
      <div
        aria-hidden
        className="flex flex-col gap-4 border-rule bg-sheet px-4 py-6 lg:border-l lg:px-8"
      >
        <div className={`${bar} h-7 w-48`} />
        <div className={`${bar} h-4 w-96 max-w-full`} />
        <div className="mt-4 h-[320px] max-w-[1180px] rounded-sm bg-code-bg" />
      </div>
    </div>
  );
}

export default function Home() {
  const [catalog, setCatalog] = useState<CatalogV2Response | null>(null);
  const [error, setError] = useState<string | null>(null);
  const initialState = useInitialPermalink();

  useEffect(() => {
    let cancelled = false;
    getCatalog()
      .then((c) => {
        if (!cancelled) setCatalog(c);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-dvh flex-col lg:h-dvh">
      <header className="flex h-14 shrink-0 items-center gap-4 border-b border-rule bg-paper px-4 lg:px-6">
        <div className="flex items-center gap-2.5 text-ink">
          <Mark className="h-6 w-6" />
          <span className="text-[17px] font-semibold tracking-[-0.01em]">SemiCraft</span>
        </div>
        <span aria-hidden className="hidden h-5 w-px bg-rule sm:block" />
        <p className="hidden text-sm text-ink-2 sm:block">
          RTL, testbenches and IP from options you choose. Same options, same bytes.
        </p>
        {catalog ? (
          <p className="ml-auto hidden font-mono text-xs text-ink-3 lg:block">
            {catalogSummary(catalog)}
          </p>
        ) : null}
      </header>

      <div className="flex-1 lg:min-h-0">
        {error ? (
          <div role="alert" className="mx-auto max-w-md px-6 py-16">
            <p className="label-caps">Catalog unavailable</p>
            <p className="mt-2 text-sm text-ink">{error}</p>
            <p className="mt-1 text-sm text-ink-2">
              Check that the API is running and NEXT_PUBLIC_API_BASE points at it.
            </p>
          </div>
        ) : catalog ? (
          <GeneratorApp catalog={catalog} initialState={initialState} />
        ) : (
          <LoadingSkeleton />
        )}
      </div>
    </div>
  );
}

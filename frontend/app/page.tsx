"use client";

import { useEffect, useState } from "react";
import type { CatalogV2Response } from "@/lib/types";
import { getCatalog } from "@/lib/api";
import { GeneratorApp, useInitialPermalink } from "@/components/GeneratorApp";
import { Mark } from "@/components/Mark";

function catalogSummary(c: CatalogV2Response): string {
  const n = (kind: string) => c.items.filter((i) => i.kind === kind).length;
  const parts = [
    [n("snippet"), "snippets"],
    [n("module"), "modules"],
    [n("ip"), "IP blocks"],
  ].filter(([count]) => (count as number) > 0);
  return parts.map(([count, noun]) => `${count} ${noun}`).join(" · ");
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
    <div className="flex min-h-screen flex-col lg:h-screen">
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
          <p className="px-6 py-16 font-mono text-xs text-ink-3">Loading catalog…</p>
        )}
      </div>
    </div>
  );
}

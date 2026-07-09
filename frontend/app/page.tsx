"use client";

import { useEffect, useState } from "react";
import type { CatalogV2Response } from "@/lib/types";
import { getCatalog } from "@/lib/api";
import { GeneratorApp, useInitialPermalink } from "@/components/GeneratorApp";

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
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-3 border-b border-zinc-200 px-4 py-2 dark:border-zinc-800">
        <h1 className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          SemiCraft
        </h1>
        <span className="text-xs text-zinc-500">RTL Snippet Generator</span>
      </header>

      <div className="min-h-0 flex-1">
        {error ? (
          <p role="alert" className="p-4 text-sm text-red-600">
            {error}
          </p>
        ) : catalog ? (
          <GeneratorApp catalog={catalog} initialState={initialState} />
        ) : (
          <p className="p-4 text-sm text-zinc-500">Loading snippets…</p>
        )}
      </div>
    </div>
  );
}

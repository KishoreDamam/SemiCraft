"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  CatalogResponse,
  GenerateResponse,
  SnippetCatalogEntry,
} from "@/lib/types";
import { generate } from "@/lib/api";
import { canonicalJson } from "@/lib/hash";
import {
  fromSearch,
  toQueryString,
  type PermalinkState,
} from "@/lib/permalink";
import { useDebouncedValue } from "@/lib/useDebouncedValue";
import { DynamicForm, type OptionValues } from "@/components/DynamicForm";
import { SnippetPicker } from "@/components/SnippetPicker";
import { CodePreview } from "@/components/CodePreview";
import { LintBadge } from "@/components/LintBadge";
import { ExplanationPanel } from "@/components/ExplanationPanel";

const DEBOUNCE_MS = 300;

function entryById(
  catalog: CatalogResponse,
  id: string | null,
): SnippetCatalogEntry | undefined {
  return catalog.snippets.find((s) => s.id === id);
}

/**
 * The whole generator experience (WP-07 tasks 1,3,4,5,6). Accepts the catalog
 * and an optional initial permalink state so the page shell can inject data
 * and tests can drive it deterministically.
 */
export function GeneratorApp({
  catalog,
  initialState,
  debounceMs = DEBOUNCE_MS,
}: {
  catalog: CatalogResponse;
  initialState?: PermalinkState | null;
  debounceMs?: number;
}) {
  const firstEntry = catalog.snippets[0];

  const initialEntry =
    (initialState && entryById(catalog, initialState.snippet_id)) || firstEntry;

  const [snippetId, setSnippetId] = useState<string>(initialEntry.id);
  const [values, setValues] = useState<OptionValues>(() =>
    initialState && entryById(catalog, initialState.snippet_id)
      ? { ...initialEntry.defaults, ...initialState.options }
      : { ...initialEntry.defaults },
  );
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [permalinkCopied, setPermalinkCopied] = useState(false);

  const entry = entryById(catalog, snippetId) ?? firstEntry;

  // Debounce the option snapshot (task 3). Serialise so value identity is
  // stable across renders with equal content.
  const snapshot = useMemo(
    () => ({ snippetId, key: canonicalJson(values) }),
    [snippetId, values],
  );
  const debounced = useDebouncedValue(snapshot, debounceMs);

  // Track the latest request so out-of-order responses are discarded.
  const reqSeq = useRef(0);

  const runGenerate = useCallback(
    async (id: string, opts: OptionValues) => {
      const seq = ++reqSeq.current;
      // Yield first so no setState runs synchronously inside the calling
      // effect body (avoids cascading-render lint; correctness unaffected).
      await Promise.resolve();
      setBusy(true);
      const res = await generate(id, opts);
      if (seq !== reqSeq.current) return; // superseded
      setBusy(false);
      if (res.ok) {
        setResult(res.data);
        setFieldErrors({});
        setGlobalError(null);
      } else if ("fieldErrors" in res) {
        setFieldErrors(res.fieldErrors);
        setGlobalError(null);
      } else {
        setGlobalError(res.message);
      }
    },
    [],
  );

  // Fire generation when the debounced snapshot changes. This is a
  // data-fetching effect: runGenerate awaits before any setState, so no state
  // updates run synchronously in the effect body despite the static rule.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runGenerate(debounced.snippetId, JSON.parse(debounced.key));
  }, [debounced, runGenerate]);

  // Keep the permalink in the URL in sync with current state (task 6).
  useEffect(() => {
    if (typeof window === "undefined") return;
    const qs = toQueryString({ snippet_id: snippetId, options: values });
    const url = `${window.location.pathname}?${qs}`;
    window.history.replaceState(null, "", url);
  }, [snippetId, values]);

  const onSelectSnippet = (id: string) => {
    const e = entryById(catalog, id);
    if (!e) return;
    setSnippetId(id);
    setValues({ ...e.defaults });
    setFieldErrors({});
    setGlobalError(null);
  };

  const onFieldChange = (name: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    // Clear the inline error for a field as soon as the user edits it.
    setFieldErrors((prev) => {
      if (!(name in prev)) return prev;
      const next = { ...prev };
      delete next[name];
      return next;
    });
  };

  const onCopy = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked; ignore */
    }
  };

  const onDownload = () => {
    if (!result) return;
    const blob = new Blob([result.code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = result.filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const onCopyPermalink = async () => {
    const qs = toQueryString({ snippet_id: snippetId, options: values });
    const href =
      typeof window !== "undefined"
        ? `${window.location.origin}${window.location.pathname}?${qs}`
        : `?${qs}`;
    try {
      await navigator.clipboard.writeText(href);
      setPermalinkCopied(true);
      setTimeout(() => setPermalinkCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="grid h-full grid-cols-1 gap-4 p-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      {/* Left panel: picker + options form */}
      <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto">
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Snippet
          </h2>
          <SnippetPicker
            snippets={catalog.snippets}
            selectedId={snippetId}
            onSelect={onSelectSnippet}
          />
        </div>
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Options
          </h2>
          <DynamicForm
            schema={entry.json_schema}
            values={values}
            errors={fieldErrors}
            onChange={onFieldChange}
          />
        </div>
      </aside>

      {/* Right panel: preview + affordances + explanation */}
      <main className="flex min-h-0 flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <LintBadge lint={result?.lint ?? null} />
          <span className="text-xs text-zinc-400">
            {result ? result.filename : ""}
            {result ? ` · ${result.config_hash}` : ""}
          </span>
          <div className="ml-auto flex items-center gap-2">
            {busy ? <span className="text-xs text-zinc-400">generating…</span> : null}
            <button
              type="button"
              onClick={onCopy}
              disabled={!result}
              className="rounded border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              type="button"
              onClick={onDownload}
              disabled={!result}
              className="rounded border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              Download
            </button>
            <button
              type="button"
              onClick={onCopyPermalink}
              className="rounded border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              {permalinkCopied ? "Link copied" : "Share link"}
            </button>
          </div>
        </div>

        {globalError ? (
          <p role="alert" className="rounded bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
            {globalError}
          </p>
        ) : null}

        <div className="min-h-[300px] flex-1">
          <CodePreview
            code={result?.code ?? "// Adjust options to generate RTL…"}
            language={result?.language ?? "sv"}
          />
        </div>

        <ExplanationPanel doc={result?.explanation ?? null} />
      </main>
    </div>
  );
}

/** Convenience wrapper: read initial permalink state from the URL on mount. */
export function useInitialPermalink(): PermalinkState | null {
  const [state] = useState<PermalinkState | null>(() => {
    if (typeof window === "undefined") return null;
    return fromSearch(window.location.search);
  });
  return state;
}

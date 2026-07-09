"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  CatalogItem,
  CatalogV2Response,
  GenerateV2Response,
} from "@/lib/types";
import { downloadZip, generateV2, saveBlob } from "@/lib/api";
import { canonicalJson } from "@/lib/hash";
import {
  fromSearch,
  toQueryString,
  type PermalinkState,
} from "@/lib/permalink";
import { useDebouncedValue } from "@/lib/useDebouncedValue";
import { DynamicForm, type OptionValues } from "@/components/DynamicForm";
import { CatalogPicker } from "@/components/CatalogPicker";
import { CodePreview } from "@/components/CodePreview";
import { FileTabs } from "@/components/FileTabs";
import { LintBadge } from "@/components/LintBadge";
import { ExplanationPanel } from "@/components/ExplanationPanel";

const DEBOUNCE_MS = 300;

function itemById(
  catalog: CatalogV2Response,
  id: string | null,
): CatalogItem | undefined {
  return catalog.items.find((s) => s.id === id);
}

/**
 * The whole generator experience, migrated to the v2 (multi-file) API in
 * P2-05b. The app runs a single code path: every item — snippet or module — is
 * generated through POST /api/v2/generate and rendered from its `files[]`.
 * Single-file results (all snippets) look identical to the pre-v2 UI; multi-
 * file results (modules) add a tab bar and a "Download .zip" button.
 */
export function GeneratorApp({
  catalog,
  initialState,
  debounceMs = DEBOUNCE_MS,
}: {
  catalog: CatalogV2Response;
  initialState?: PermalinkState | null;
  debounceMs?: number;
}) {
  const firstItem = catalog.items[0];

  const initialItem =
    (initialState && itemById(catalog, initialState.snippet_id)) || firstItem;

  const [itemId, setItemId] = useState<string>(initialItem.id);
  const [values, setValues] = useState<OptionValues>(() =>
    initialState && itemById(catalog, initialState.snippet_id)
      ? { ...initialItem.defaults, ...initialState.options }
      : { ...initialItem.defaults },
  );
  const [result, setResult] = useState<GenerateV2Response | null>(null);
  const [activeFile, setActiveFile] = useState(0);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [permalinkCopied, setPermalinkCopied] = useState(false);

  const item = itemById(catalog, itemId) ?? firstItem;

  // Debounce the option snapshot. Serialise so value identity is stable across
  // renders with equal content.
  const snapshot = useMemo(
    () => ({ itemId, key: canonicalJson(values) }),
    [itemId, values],
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
      const res = await generateV2(id, opts);
      if (seq !== reqSeq.current) return; // superseded
      setBusy(false);
      if (res.ok) {
        setResult(res.data);
        setActiveFile((prev) => (prev < res.data.files.length ? prev : 0));
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
    void runGenerate(debounced.itemId, JSON.parse(debounced.key));
  }, [debounced, runGenerate]);

  // Keep the permalink in the URL in sync with current state. The permalink
  // format is unchanged (field name `snippet_id`); it round-trips any item id,
  // modules included.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const qs = toQueryString({ snippet_id: itemId, options: values });
    const url = `${window.location.pathname}?${qs}`;
    window.history.replaceState(null, "", url);
  }, [itemId, values]);

  const onSelectItem = (id: string) => {
    const e = itemById(catalog, id);
    if (!e) return;
    setItemId(id);
    setValues({ ...e.defaults });
    setActiveFile(0);
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

  const files = result?.files ?? [];
  const current = files[activeFile] ?? files[0] ?? null;
  const isMultiFile = files.length > 1;

  const onCopy = async () => {
    if (!current) return;
    try {
      await navigator.clipboard.writeText(current.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked; ignore */
    }
  };

  const onDownload = () => {
    if (!current) return;
    const blob = new Blob([current.text], { type: "text/plain" });
    saveBlob(blob, current.path);
  };

  const onDownloadZip = async () => {
    if (!result) return;
    try {
      await downloadZip(itemId, values);
    } catch {
      setGlobalError("Zip download failed.");
    }
  };

  const onCopyPermalink = async () => {
    const qs = toQueryString({ snippet_id: itemId, options: values });
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

  const previewLanguage =
    current?.kind === "doc" ? "markdown" : result?.language ?? "sv";

  return (
    <div className="grid h-full grid-cols-1 gap-4 p-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      {/* Left panel: picker + options form */}
      <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto">
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Catalog
          </h2>
          <CatalogPicker
            items={catalog.items}
            selectedId={itemId}
            onSelect={onSelectItem}
          />
        </div>
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Options
          </h2>
          <DynamicForm
            schema={item.json_schema}
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
            {current ? current.path : ""}
            {result ? ` · ${result.config_hash}` : ""}
          </span>
          <div className="ml-auto flex items-center gap-2">
            {busy ? <span className="text-xs text-zinc-400">generating…</span> : null}
            <button
              type="button"
              onClick={onCopy}
              disabled={!current}
              className="rounded border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              {copied ? "Copied" : "Copy"}
            </button>
            {isMultiFile ? (
              <button
                type="button"
                onClick={onDownloadZip}
                disabled={!result}
                className="rounded border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
              >
                Download .zip
              </button>
            ) : (
              <button
                type="button"
                onClick={onDownload}
                disabled={!current}
                className="rounded border border-zinc-300 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
              >
                Download
              </button>
            )}
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

        <FileTabs
          files={files}
          activeIndex={activeFile}
          onSelect={setActiveFile}
        />

        <div className="min-h-[300px] flex-1">
          <CodePreview
            code={current?.text ?? "// Adjust options to generate RTL…"}
            language={previewLanguage}
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

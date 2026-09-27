"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  CatalogItem,
  CatalogV2Response,
  GenerateV2Response,
  SimulateResponse,
} from "@/lib/types";
import { downloadZip, generateV2, saveBlob, simulate } from "@/lib/api";
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
import { Lamp, LintBadge } from "@/components/LintBadge";
import { SimPanel } from "@/components/SimPanel";
import { ExplanationPanel } from "@/components/ExplanationPanel";

const DEBOUNCE_MS = 300;

/**
 * What a first visit opens on: a plain snippet rather than whatever sorts
 * first (alphabetically that is a beta AXI IP with seven files). Counter is
 * the PRD's lead user story; any snippet will do if it is absent.
 */
function defaultItem(catalog: CatalogV2Response): CatalogItem {
  return (
    itemById(catalog, "counter") ??
    catalog.items.find((i) => i.kind === "snippet") ??
    catalog.items[0]
  );
}

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
  const firstItem = defaultItem(catalog);

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
  const [simResult, setSimResult] = useState<SimulateResponse | null>(null);
  const [simBusy, setSimBusy] = useState(false);

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
        // A fresh generation invalidates any prior sim result (it was for the
        // previous config); clear it so the log viewer never shows stale output.
        setSimResult(null);
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
    setSimResult(null);
  };

  const onFieldChange = (name: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    // Clear the inline error for a field as soon as the user edits it. A
    // nested sub-model reports errors under its own keys (422 loc ends in the
    // sub-field), so editing it clears those too.
    const keys =
      value && typeof value === "object" && !Array.isArray(value)
        ? [name, ...Object.keys(value)]
        : [name];
    setFieldErrors((prev) => {
      if (!keys.some((k) => k in prev)) return prev;
      const next = { ...prev };
      for (const k of keys) delete next[k];
      return next;
    });
  };

  const files = result?.files ?? [];
  const current = files[activeFile] ?? files[0] ?? null;
  const isMultiFile = files.length > 1;
  // Snippets carry no testbench; the sim endpoint would only answer "no_tb".
  const hasTb = item.kind !== "snippet";
  // A 422 leaves the previous result on screen; say so rather than let the
  // preview and explanation silently describe a different configuration.
  const stale = result !== null && Object.keys(fieldErrors).length > 0;

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

  const onRunSim = async () => {
    if (!result) return;
    setSimBusy(true);
    setSimResult(null);
    const res = await simulate(itemId, values);
    setSimBusy(false);
    if (res.ok) {
      setSimResult(res.data);
    } else {
      setGlobalError(res.message);
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

  const onResetDefaults = () => {
    setValues({ ...item.defaults });
    setFieldErrors({});
  };

  const lineCount = current ? current.text.split("\n").length : 0;

  return (
    <div className="grid grid-cols-1 lg:h-full lg:grid-cols-[320px_minmax(0,1fr)]">
      {/* Left column: catalog + options */}
      <aside className="flex flex-col gap-7 px-4 py-5 lg:min-h-0 lg:overflow-y-auto lg:px-5">
        <section className="flex flex-col gap-2.5">
          <h2 className="label-caps">Catalog</h2>
          <CatalogPicker
            items={catalog.items}
            selectedId={itemId}
            onSelect={onSelectItem}
          />
        </section>
        <section className="flex flex-col gap-3 border-t border-rule pt-5">
          <div className="flex items-baseline justify-between">
            <h2 className="label-caps">Options</h2>
            <button
              type="button"
              onClick={onResetDefaults}
              className="rounded-sm font-mono text-[11px] text-ink-3 hover:text-ink hover:underline"
            >
              Reset to defaults
            </button>
          </div>
          <DynamicForm
            schema={item.json_schema}
            values={values}
            errors={fieldErrors}
            onChange={onFieldChange}
          />
        </section>
      </aside>

      {/* Right column: the datasheet for the current configuration */}
      <main className="flex flex-col border-rule bg-sheet lg:min-h-0 lg:overflow-y-auto lg:border-l">
        <header className="flex flex-col gap-4 border-b border-rule px-4 pb-5 pt-6 lg:px-8">
          <div className="flex flex-wrap items-start gap-x-6 gap-y-4">
            <div className="min-w-0 flex-1 basis-80">
              <h1 className="text-[28px] font-semibold leading-tight tracking-[-0.02em] text-ink">
                {item.name}
              </h1>
              <p className="mt-1.5 max-w-[68ch] text-[15px] leading-relaxed text-ink-2">
                {item.description}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={onRunSim}
                disabled={!result || !hasTb || simBusy}
                title={
                  !hasTb
                    ? "Snippets have no testbench; pick a module or IP block to simulate."
                    : undefined
                }
                className={BTN_SECONDARY}
              >
                {simBusy ? "Running…" : "Run smoke sim"}
              </button>
              <button type="button" onClick={onCopyPermalink} className={BTN_SECONDARY}>
                {permalinkCopied ? "Link copied" : "Share link"}
              </button>
              {isMultiFile ? (
                <button
                  type="button"
                  onClick={onDownloadZip}
                  disabled={!result}
                  className={BTN_PRIMARY}
                >
                  Download .zip
                </button>
              ) : (
                <button
                  type="button"
                  onClick={onDownload}
                  disabled={!current}
                  className={BTN_PRIMARY}
                >
                  Download
                </button>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-xs text-ink-3">
            <LintBadge lint={result?.lint ?? null} />
            <dl className="contents">
              <Fact term="Kind" value={KIND_LABEL[item.kind] ?? item.kind} />
              <Fact
                term="Maturity"
                value={item.maturity}
                className={item.maturity === "beta" ? "text-warn" : undefined}
              />
              {result ? <Fact term="Config" value={result.config_hash} /> : null}
              {isMultiFile ? <Fact term="Files" value={String(files.length)} /> : null}
            </dl>
            {busy ? <span aria-live="polite">generating…</span> : null}
          </div>
        </header>

        <div className="flex flex-col gap-6 px-4 py-6 lg:px-8">
          {globalError ? (
            <p role="alert" className="flex items-center gap-2 text-sm text-err">
              <Lamp tone="err" /> {globalError}
            </p>
          ) : null}

          {stale ? (
            <p role="status" className="flex items-center gap-2 text-sm text-warn">
              <Lamp tone="warn" /> Fix the highlighted option to regenerate. Showing the last
              valid result.
            </p>
          ) : null}

          <div className="flex flex-col overflow-hidden rounded-sm border border-rule-strong">
            <div className="flex h-10 items-center gap-2 border-b border-black/40 bg-code-strip pr-2">
              {isMultiFile ? (
                <FileTabs files={files} activeIndex={activeFile} onSelect={setActiveFile} />
              ) : (
                <span className="min-w-0 flex-1 truncate px-4 font-mono text-xs text-code-ink">
                  {current?.path ?? ""}
                </span>
              )}
              {current && !isMultiFile ? (
                <span className="hidden shrink-0 font-mono text-[11px] text-code-ink-3 sm:inline">
                  {lineCount} lines
                </span>
              ) : null}
              <button
                type="button"
                onClick={onCopy}
                disabled={!current}
                className="ml-1 h-7 shrink-0 rounded-sm border-l border-black/40 px-3 font-mono text-xs text-code-ink hover:bg-code-ink hover:text-code-bg disabled:text-code-ink-3"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <div className="h-[60vh] min-h-[360px]">
              <CodePreview
                code={current?.text ?? "// Adjust options to generate RTL…"}
                language={previewLanguage}
              />
            </div>
          </div>

          <SimPanel result={simResult} />

          <ExplanationPanel doc={result?.explanation ?? null} />
        </div>
      </main>
    </div>
  );
}

const BTN_BASE =
  "inline-flex h-9 items-center rounded-sm px-3.5 text-[13px] font-medium active:translate-y-px disabled:pointer-events-none";
const BTN_SECONDARY = `${BTN_BASE} border border-rule-strong bg-sheet text-ink hover:border-ink hover:bg-well disabled:border-rule disabled:bg-transparent disabled:text-ink-3`;
const BTN_PRIMARY = `${BTN_BASE} border border-ink bg-ink text-paper hover:border-accent hover:bg-accent hover:text-accent-ink disabled:border-rule disabled:bg-well disabled:text-ink-3`;

const KIND_LABEL: Record<string, string> = {
  snippet: "snippet",
  module: "module",
  ip: "IP block",
};

function Fact({
  term,
  value,
  className,
}: {
  term: string;
  value: string;
  className?: string;
}) {
  return (
    <div className="flex items-baseline gap-1.5">
      <dt>{term}</dt>
      <dd className={className ?? "text-ink"}>{value}</dd>
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

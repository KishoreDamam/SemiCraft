"use client";

import { useEffect, useState } from "react";
import Editor, { loader } from "@monaco-editor/react";

// Serve Monaco from this app (copied into public/ by scripts/copy-monaco.mjs)
// instead of the loader's default CDN, which restricted networks block.
loader.config({ paths: { vs: "/monaco/vs" } });

/**
 * Read-only code preview. Monaco has no dedicated "systemverilog" language id;
 * "verilog" is the closest built-in grammar and highlights SV reasonably, so
 * both HDL targets map onto it.
 *
 * The generated text is visible at all times: while Monaco loads — and for
 * good if it cannot load — the same code renders as plain monospace text.
 * The preview is the product; a blank "Loading…" box is never acceptable.
 */
export function CodePreview({
  code,
  language,
}: {
  code: string;
  language: "sv" | "verilog" | "markdown";
}) {
  const [editorFailed, setEditorFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // loader.init() is memoised, so this shares the Editor's own load.
    loader.init().catch(() => {
      if (!cancelled) setEditorFailed(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Doc files pass "markdown" and get Monaco's built-in markdown grammar.
  const monacoLang = language === "markdown" ? "markdown" : "verilog";

  const plain = (
    <pre
      data-testid="code-plain"
      className="h-full w-full overflow-auto bg-[#1e1e1e] p-3 font-mono text-[13px] leading-[19px] text-zinc-200"
    >
      {code}
    </pre>
  );

  return (
    <div className="h-full min-h-[300px] w-full overflow-hidden rounded border border-zinc-200 dark:border-zinc-800">
      {editorFailed ? (
        plain
      ) : (
        <Editor
          height="100%"
          language={monacoLang}
          value={code}
          theme="vs-dark"
          loading={plain}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: "off",
            renderLineHighlight: "none",
          }}
        />
      )}
    </div>
  );
}

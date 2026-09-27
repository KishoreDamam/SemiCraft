"use client";

import { useEffect, useState } from "react";
import Editor, { loader, type Monaco } from "@monaco-editor/react";

// Serve Monaco from this app (copied into public/ by scripts/copy-monaco.mjs)
// instead of the loader's default CDN, which restricted networks block.
loader.config({ paths: { vs: "/monaco/vs" } });

const THEME = "semicraft";

/** Editor theme drawn from the app palette (globals.css code tokens). */
function defineTheme(monaco: Monaco) {
  monaco.editor.defineTheme(THEME, {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "8f8a7e" },
      { token: "keyword", foreground: "e59a74" },
      { token: "type", foreground: "d8c48f" },
      { token: "number", foreground: "a6cfa5" },
      { token: "string", foreground: "c9d7a0" },
      { token: "delimiter", foreground: "b9b4a6" },
      { token: "identifier", foreground: "e9e5da" },
    ],
    colors: {
      "editor.background": "#1b1a17",
      "editor.foreground": "#e9e5da",
      "editorLineNumber.foreground": "#5f5b52",
      "editorLineNumber.activeForeground": "#5f5b52",
      "editor.selectionBackground": "#a4481f66",
      "editor.inactiveSelectionBackground": "#a4481f33",
      "editorIndentGuide.background1": "#2c2b26",
      "editorCursor.foreground": "#e08257",
      // Belt and braces with bracketPairColorization: neutral pair colours.
      ...Object.fromEntries(
        [1, 2, 3, 4, 5, 6].map((n) => [`editorBracketHighlight.foreground${n}`, "#b9b4a6"]),
      ),
      "scrollbarSlider.background": "#e9e5da1f",
      "scrollbarSlider.hoverBackground": "#e9e5da33",
    },
  });
}

/**
 * Read-only code preview. Monaco has no dedicated "systemverilog" language id;
 * "verilog" is the closest built-in grammar and highlights SV reasonably, so
 * both HDL targets map onto it.
 *
 * The generated text is visible at all times: while Monaco loads, and for
 * good if it cannot load, the same code renders as plain monospace text.
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
      className="h-full w-full overflow-auto bg-code-bg px-4 py-3 font-mono text-[13px] leading-[20px] text-code-ink"
    >
      {code}
    </pre>
  );

  return (
    <div className="h-full w-full overflow-hidden bg-code-bg">
      {editorFailed ? (
        plain
      ) : (
        <Editor
          height="100%"
          language={monacoLang}
          value={code}
          theme={THEME}
          beforeMount={defineTheme}
          loading={plain}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
            fontSize: 13,
            lineHeight: 20,
            padding: { top: 12, bottom: 12 },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: "off",
            renderLineHighlight: "none",
            // Verilog's begin/end count as brackets; rainbow pairs fight the palette.
            bracketPairColorization: { enabled: false },
            matchBrackets: "never",
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            guides: { indentation: false },
            scrollbar: { verticalScrollbarSize: 10, horizontalScrollbarSize: 10 },
          }}
        />
      )}
    </div>
  );
}

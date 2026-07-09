"use client";

import Editor from "@monaco-editor/react";

/**
 * Read-only Monaco code preview (WP-07 task 1). Monaco has no dedicated
 * "systemverilog" language id; "verilog" is the closest built-in grammar and
 * highlights SV reasonably. We map both HDL targets onto it.
 */
export function CodePreview({
  code,
  language,
}: {
  code: string;
  language: "sv" | "verilog" | "markdown";
}) {
  // Monaco ships a "verilog" grammar; use it for both HDL targets. Doc files
  // pass "markdown" and get Monaco's built-in markdown grammar.
  const monacoLang = language === "markdown" ? "markdown" : "verilog";

  return (
    <div className="h-full min-h-[300px] w-full overflow-hidden rounded border border-zinc-200 dark:border-zinc-800">
      <Editor
        height="100%"
        language={monacoLang}
        value={code}
        theme="vs-dark"
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
    </div>
  );
}

#!/usr/bin/env node
// Integration check: exercise the REAL backend (§4 contract) end-to-end.
//
//   1. Start the backend:  uv run uvicorn api.main:app --port 8000 --app-dir backend
//   2. Run this script:    node scripts/integration-check.mjs
//
// For every registered snippet it POSTs /api/v1/generate with the snippet's
// own defaults and asserts a 200 with non-empty code, a structured
// explanation, and a lint status in {clean, warnings, unavailable}. It also
// verifies one 422 path (counter width=0) returns the FastAPI envelope the
// frontend's fieldErrorsFrom() parses. Exit code is non-zero on any failure.

const BASE = process.env.API_BASE ?? "http://localhost:8000";
const LINT_OK = new Set(["clean", "warnings", "unavailable"]);

let failures = 0;
const rows = [];

function check(cond, msg) {
  if (!cond) {
    failures += 1;
    console.error("  FAIL:", msg);
  }
  return cond;
}

async function main() {
  const catRes = await fetch(`${BASE}/api/v1/snippets`, {
    headers: { accept: "application/json" },
  });
  check(catRes.ok, `GET /api/v1/snippets -> ${catRes.status}`);
  const catalog = await catRes.json();
  check(
    Array.isArray(catalog.snippets) && catalog.snippets.length === 10,
    `expected 10 snippets, got ${catalog.snippets?.length}`,
  );

  for (const s of catalog.snippets) {
    const res = await fetch(`${BASE}/api/v1/generate`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ snippet_id: s.id, options: s.defaults }),
    });
    const status = res.status;
    let lint = "-";
    let codeLen = 0;
    let hasExpl = false;
    if (status === 200) {
      const body = await res.json();
      codeLen = (body.code ?? "").length;
      lint = body.lint?.status ?? "?";
      hasExpl =
        body.explanation &&
        typeof body.explanation === "object" &&
        typeof body.explanation.purpose === "string";
      check(status === 200, `${s.id}: status ${status}`);
      check(codeLen > 0, `${s.id}: empty code`);
      check(hasExpl, `${s.id}: missing/invalid explanation`);
      check(LINT_OK.has(lint), `${s.id}: bad lint status "${lint}"`);
      check(typeof body.config_hash === "string" && body.config_hash.length === 12,
        `${s.id}: config_hash not 12 hex chars (${body.config_hash})`);
      check(body.language === "sv" || body.language === "verilog",
        `${s.id}: bad language ${body.language}`);
    } else {
      check(false, `${s.id}: expected 200, got ${status}`);
    }
    rows.push({ snippet: s.id, status, code: codeLen, lint, expl: hasExpl });
  }

  // --- 422 path: counter width=0 ---
  const badRes = await fetch(`${BASE}/api/v1/generate`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ snippet_id: "counter", options: { width: 0 } }),
  });
  check(badRes.status === 422, `counter width=0: expected 422, got ${badRes.status}`);
  const badBody = await badRes.json();
  const item = badBody.detail?.[0];
  check(Array.isArray(item?.loc), "422: detail[0].loc not an array");
  check(item?.loc?.includes("width"), "422: loc does not include field 'width'");
  check(typeof item?.msg === "string" && item.msg.length > 0, "422: empty msg");
  rows.push({ snippet: "counter (width=0)", status: badRes.status, code: "-", lint: "-", expl: "-" });

  // --- 404 path ---
  const nf = await fetch(`${BASE}/api/v1/generate`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ snippet_id: "does-not-exist", options: {} }),
  });
  check(nf.status === 404, `unknown snippet: expected 404, got ${nf.status}`);
  rows.push({ snippet: "unknown (404)", status: nf.status, code: "-", lint: "-", expl: "-" });

  console.log("\nIntegration results:");
  console.table(rows);

  if (failures > 0) {
    console.error(`\n${failures} check(s) FAILED`);
    process.exit(1);
  }
  console.log("\nAll integration checks passed.");
}

main().catch((e) => {
  console.error("integration script error:", e);
  process.exit(1);
});

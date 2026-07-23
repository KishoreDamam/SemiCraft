// Types mirroring the FROZEN API contract in docs/IMPLEMENTATION_PLAN.md §4.
// The frontend builds against these exactly. Do not diverge without flagging.

/**
 * A minimal subset of JSON Schema (draft 2020-12 style, as emitted by
 * Pydantic v2 `model_json_schema()`) that the dynamic form renderer needs.
 *
 * Pydantic emits an object schema whose `properties` map field names to
 * per-field schemas. Enums, bounds and descriptions live on those per-field
 * schemas (sometimes indirected through `$defs` + `allOf`/`$ref`, sometimes
 * inline via `enum`). The renderer resolves both shapes; see lib/schema.ts.
 */
export interface JsonSchema {
  type?: JsonSchemaType | JsonSchemaType[];
  properties?: Record<string, JsonSchema>;
  required?: string[];
  // object-level
  $defs?: Record<string, JsonSchema>;
  // field-level
  title?: string;
  description?: string;
  default?: unknown;
  enum?: unknown[];
  // numeric bounds (Pydantic uses the inclusive/exclusive variants)
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
  exclusiveMaximum?: number;
  // array
  items?: JsonSchema;
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  // indirection
  $ref?: string;
  allOf?: JsonSchema[];
  anyOf?: JsonSchema[];
  // const (single-value enum sometimes emitted this way)
  const?: unknown;
}

export type JsonSchemaType =
  | "object"
  | "array"
  | "string"
  | "integer"
  | "number"
  | "boolean"
  | "null";

/** One snippet entry from GET /api/v1/snippets. */
export interface SnippetCatalogEntry {
  id: string;
  name: string;
  description: string;
  json_schema: JsonSchema;
  defaults: Record<string, unknown>;
}

export interface CatalogResponse {
  snippets: SnippetCatalogEntry[];
}

/** Body for POST /api/v1/generate. */
export interface GenerateRequest {
  snippet_id: string;
  options: Record<string, unknown>;
}

export type LintStatus = "clean" | "warnings" | "unavailable";

export interface LintMessage {
  severity: string;
  code: string;
  line: number;
  text: string;
}

export interface LintReport {
  status: LintStatus;
  messages: LintMessage[];
}

export interface SignalDoc {
  name: string;
  direction: string;
  description: string;
}

/** ExplanationDoc per §3 of the plan. */
export interface ExplanationDoc {
  purpose: string;
  configuration: string[];
  signals: SignalDoc[];
  reset_behavior: string;
  enable_behavior: string | null;
  assumptions: string[];
  limitations: string[];
}

/** 200 body for POST /api/v1/generate. */
export interface GenerateResponse {
  code: string;
  filename: string;
  language: "sv" | "verilog";
  explanation: ExplanationDoc;
  lint: LintReport;
  config_hash: string;
}

/** Shape of a single Pydantic v2 validation error (422 detail item). */
export interface ValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/** 422 body — FastAPI wraps Pydantic errors under `detail`. */
export interface ValidationErrorResponse {
  detail: ValidationErrorItem[];
}

/** Discriminated result of a generate call so callers can map 422 inline. */
export type GenerateResult =
  | { ok: true; data: GenerateResponse }
  | { ok: false; status: 422; fieldErrors: Record<string, string> }
  | { ok: false; status: number; message: string };

// ---------------------------------------------------------------------------
// API v2 (multi-file). See docs/PLAN-semicraft-phases-2-8.md Appendix A.1.
// ---------------------------------------------------------------------------

/** Item taxonomy in the v2 catalog. More kinds land in later phases. */
export type ItemKind = "snippet" | "module";

export type Maturity = "stable" | "beta";

/** One entry from GET /api/v2/catalog. Superset of SnippetCatalogEntry. */
export interface CatalogItem extends SnippetCatalogEntry {
  kind: ItemKind;
  maturity: Maturity;
}

export interface CatalogV2Response {
  items: CatalogItem[];
}

/** Kind of a generated file. `tb` is reserved (P2-13); not emitted yet. */
export type FileKind = "rtl" | "tb" | "doc";

export interface GeneratedFile {
  path: string;
  kind: FileKind;
  text: string;
}

/** Per-file lint entry — v2 lint is a LIST, one entry per rtl file. */
export interface LintFileReport extends LintReport {
  path: string;
}

/** Body for POST /api/v2/generate and /api/v2/generate/zip. */
export interface GenerateV2Request {
  item_id: string;
  options: Record<string, unknown>;
}

/** 200 body for POST /api/v2/generate. */
export interface GenerateV2Response {
  files: GeneratedFile[];
  explanation: ExplanationDoc;
  lint: LintFileReport[];
  config_hash: string;
  language: "sv" | "verilog";
}

/** Discriminated result of a v2 generate call, mirroring GenerateResult. */
export type GenerateV2Result =
  | { ok: true; data: GenerateV2Response }
  | { ok: false; status: 422; fieldErrors: Record<string, string> }
  | { ok: false; status: number; message: string };

/** A zip blob plus the filename parsed from Content-Disposition. */
export interface ZipDownload {
  blob: Blob;
  filename: string;
}

// ---------------------------------------------------------------------------
// Sim sandbox (P3-03). POST /api/v2/simulate runs an item's smoke testbench.
// ---------------------------------------------------------------------------

/**
 * Outcome of a smoke-sim run:
 *  - `pass` — compiled, ran, exited 0, printed the SMOKE PASS marker;
 *  - `fail` — compiled + ran but a check failed / marker never printed;
 *  - `unavailable` — no verilator in this environment (local dev degradation);
 *  - `error` — compile error or timeout (couldn't get a clean pass/fail read);
 *  - `no_tb` — the item generated no testbench (snippet, or clock-less module).
 */
export type SimStatus = "pass" | "fail" | "unavailable" | "error" | "no_tb";

/** 200 body for POST /api/v2/simulate. */
export interface SimulateResponse {
  status: SimStatus;
  exit_code: number | null;
  stdout_tail: string;
  stderr_tail: string;
  duration_s: number;
  marker_seen: boolean;
}

/** Discriminated result of a simulate call, mirroring GenerateV2Result. */
export type SimulateResult =
  | { ok: true; data: SimulateResponse }
  | { ok: false; status: number; message: string };

import type {
  ExplanationDoc,
  GenerateResponse,
  GenerateV2Response,
  GeneratedFile,
  JsonSchema,
  LintFileReport,
  LintReport,
  ValidationErrorItem,
  ZipDownload,
} from "@/lib/types";
import { configHash } from "@/lib/hash";
import { mockCatalog, mockCatalogV2 } from "@/mocks/catalog";
import { flattenSchema } from "@/lib/schema";

/**
 * Mock backend for POST /api/v1/generate. Produces responses that match the
 * §4 contract shape exactly:
 *  - validates options against the snippet's JSON Schema, returning Pydantic-
 *    style 422 error items on constraint violations (so the UI's inline error
 *    mapping is exercisable end-to-end);
 *  - emits plausible RTL per snippet;
 *  - computes the real config_hash;
 *  - varies lint status to exercise all three badge states.
 *
 * This is deliberately NOT a faithful reimplementation of the backend
 * generator — it produces representative output for UI development only.
 */

export class MockValidationError extends Error {
  constructor(public items: ValidationErrorItem[]) {
    super("validation error");
    this.name = "MockValidationError";
  }
}

export class MockNotFoundError extends Error {}

function getEntry(snippetId: string) {
  const entry = mockCatalog.snippets.find((s) => s.id === snippetId);
  if (!entry) throw new MockNotFoundError(snippetId);
  return entry;
}

/** Validate a value against a (flattened) field schema; push 422 items. */
function validateField(
  name: string,
  raw: JsonSchema,
  root: JsonSchema,
  value: unknown,
  errors: ValidationErrorItem[],
) {
  const s = flattenSchema(raw, root);
  const type = Array.isArray(s.type) ? s.type[0] : s.type;

  if (value === undefined || value === null) return; // defaults fill in server-side

  if (s.enum && !s.enum.includes(value as never)) {
    errors.push({
      loc: [name],
      msg: `Input should be ${s.enum.map((e) => `'${e}'`).join(", ")}`,
      type: "enum",
    });
    return;
  }

  if (type === "integer" || type === "number") {
    const n = Number(value);
    if (Number.isNaN(n)) {
      errors.push({ loc: [name], msg: "Input should be a valid number", type: "int_type" });
      return;
    }
    if (type === "integer" && !Number.isInteger(n)) {
      errors.push({ loc: [name], msg: "Input should be a valid integer", type: "int_parsing" });
    }
    if (s.minimum !== undefined && n < s.minimum) {
      errors.push({
        loc: [name],
        msg: `Input should be greater than or equal to ${s.minimum}`,
        type: "greater_than_equal",
      });
    }
    if (s.maximum !== undefined && n > s.maximum) {
      errors.push({
        loc: [name],
        msg: `Input should be less than or equal to ${s.maximum}`,
        type: "less_than_equal",
      });
    }
  }

  if (type === "array" && Array.isArray(value)) {
    if (s.minItems !== undefined && value.length < s.minItems) {
      errors.push({
        loc: [name],
        msg: `List should have at least ${s.minItems} item(s)`,
        type: "too_short",
      });
    }
    if (s.maxItems !== undefined && value.length > s.maxItems) {
      errors.push({
        loc: [name],
        msg: `List should have at most ${s.maxItems} item(s)`,
        type: "too_long",
      });
    }
    if (s.uniqueItems && new Set(value.map(String)).size !== value.length) {
      errors.push({ loc: [name], msg: "List items must be unique", type: "unique" });
    }
    const itemSchema = s.items ? flattenSchema(s.items, root) : undefined;
    if (itemSchema?.enum) {
      for (const item of value) {
        if (!itemSchema.enum.includes(item as never)) {
          errors.push({
            loc: [name],
            msg: `'${item}' is not an allowed value`,
            type: "enum",
          });
        }
      }
    }
  }
}

/** Snippet-specific cross-field checks (mirror backend model_validators). */
function crossFieldValidate(
  snippetId: string,
  opts: Record<string, unknown>,
  errors: ValidationErrorItem[],
) {
  if (snippetId === "counter") {
    const width = Number(opts.width ?? 8);
    const rv = Number(opts.reset_value ?? 0);
    if (Number.isFinite(width) && Number.isFinite(rv) && rv >= 2 ** Math.min(width, 53)) {
      errors.push({
        loc: ["reset_value"],
        msg: `reset_value must be less than 2^width (${2 ** Math.min(width, 53)})`,
        type: "value_error",
      });
    }
  }
  if (snippetId === "fsm") {
    const states = (opts.states as string[] | undefined) ?? [];
    const resetState = opts.reset_state as string | undefined;
    if (resetState !== undefined && resetState !== "" && !states.includes(resetState)) {
      errors.push({
        loc: ["reset_state"],
        msg: `reset_state '${resetState}' must be one of the declared states`,
        type: "value_error",
      });
    }
    const ident = /^[A-Za-z_][A-Za-z0-9_]*$/;
    for (const st of states) {
      if (!ident.test(st)) {
        errors.push({
          loc: ["states"],
          msg: `'${st}' is not a valid identifier`,
          type: "value_error",
        });
        break;
      }
    }
  }
}

function ext(language: unknown): string {
  return language === "verilog" ? "v" : "sv";
}

// ---- RTL emitters (representative, not the real generator) ----

const HEADER = (name: string, hash: string, lang: string) =>
  [
    `// -----------------------------------------------------------------------------`,
    `// SemiCraft (mock) — ${name}`,
    `// language: ${lang}   config_hash: ${hash}`,
    `// Generated code is provided as-is, without warranty of any kind. Free for`,
    `// commercial and non-commercial use at the user's own risk.`,
    `// -----------------------------------------------------------------------------`,
    ``,
  ].join("\n");

function rstName(opts: Record<string, unknown>): string {
  return opts.reset_polarity === "active_high" ? "rst" : "rst_n";
}

function emitCounter(opts: Record<string, unknown>): string {
  const width = Number(opts.width ?? 8);
  const sv = opts.language !== "verilog";
  const rst = rstName(opts);
  const en = opts.enable === true;
  const async = opts.reset_style === "async";
  const rstEdge = async
    ? opts.reset_polarity === "active_high"
      ? ` or posedge ${rst}`
      : ` or negedge ${rst}`
    : "";
  const rstTest = opts.reset_polarity === "active_high" ? rst : `!${rst}`;
  const step = opts.direction === "down" ? "count - 1'b1" : "count + 1'b1";
  const alwaysKw = sv ? "always_ff" : "always";
  const decl = sv
    ? `  logic [WIDTH-1:0] count;`
    : `  reg [WIDTH-1:0] count;`;
  return [
    `module counter #(`,
    `  parameter int WIDTH = ${width}`,
    `) (`,
    `  input  wire             clk,`,
    `  input  wire             ${rst},`,
    en ? `  input  wire             en,` : null,
    opts.direction === "updown" ? `  input  wire             up_dn,` : null,
    `  output ${sv ? "logic" : "reg  "} [WIDTH-1:0] count_o`,
    `);`,
    ``,
    decl,
    ``,
    `  ${alwaysKw} @(posedge clk${rstEdge}) begin`,
    `    if (${rstTest}) begin`,
    `      count <= ${Number(opts.reset_value ?? 0)};`,
    `    end${en ? " else if (en) begin" : " else begin"}`,
    `      count <= ${step};`,
    `    end`,
    `  end`,
    ``,
    `  assign count_o = count;`,
    ``,
    `endmodule`,
    ``,
  ]
    .filter((l): l is string => l !== null)
    .join("\n");
}

function emitFsm(opts: Record<string, unknown>): string {
  const sv = opts.language !== "verilog";
  const states = ((opts.states as string[] | undefined) ?? ["idle"]).slice();
  const reset = (opts.reset_state as string | undefined) ?? states[0];
  const rst = rstName(opts);
  const outputs = (opts.outputs as string[] | undefined) ?? [];
  const stateType = sv ? "state_e" : "reg [ST_W-1:0]";
  const lines: string[] = [];
  lines.push(`module fsm (`);
  lines.push(`  input  wire clk,`);
  lines.push(`  input  wire ${rst},`);
  for (const o of outputs) lines.push(`  output reg  ${o},`);
  lines.push(`  output wire fsm_active`);
  lines.push(`);`);
  lines.push(``);
  if (sv) {
    lines.push(`  typedef enum logic [${Math.max(0, Math.ceil(Math.log2(states.length)) - 1)}:0] {`);
    lines.push(
      states
        .map((s, i) => `    ${s.toUpperCase()} = ${i}`)
        .join(",\n"),
    );
    lines.push(`  } state_e;`);
    lines.push(`  state_e state, state_next;`);
  } else {
    const w = Math.max(1, Math.ceil(Math.log2(states.length)));
    lines.push(`  localparam ST_W = ${w};`);
    states.forEach((s, i) => lines.push(`  localparam [ST_W-1:0] ${s.toUpperCase()} = ${i};`));
    lines.push(`  ${stateType} state, state_next;`);
  }
  lines.push(``);
  lines.push(`  // State register`);
  lines.push(`  ${sv ? "always_ff" : "always"} @(posedge clk) begin`);
  lines.push(`    if (${opts.reset_polarity === "active_high" ? rst : `!${rst}`}) state <= ${reset.toUpperCase()};`);
  lines.push(`    else state <= state_next;`);
  lines.push(`  end`);
  lines.push(``);
  lines.push(`  // Next-state logic (transitions to be completed by the user)`);
  lines.push(`  ${sv ? "always_comb" : "always @(*)"} begin`);
  lines.push(`    state_next = state;`);
  lines.push(`    case (state)`);
  for (const s of states) {
    lines.push(`      ${s.toUpperCase()}: begin`);
    lines.push(`        // TODO: transition logic for ${s}`);
    lines.push(`      end`);
  }
  lines.push(`    endcase`);
  lines.push(`  end`);
  lines.push(``);
  lines.push(`  assign fsm_active = 1'b1;`);
  lines.push(``);
  lines.push(`endmodule`);
  lines.push(``);
  return lines.join("\n");
}

function emitGeneric(id: string, name: string, opts: Record<string, unknown>): string {
  const sv = opts.language !== "verilog";
  const modName = id.replace(/-/g, "_");
  return [
    `module ${modName} (`,
    `  // ${name} — representative mock output`,
    `  input  wire in_a,`,
    `  input  wire in_b,`,
    `  output ${sv ? "logic" : "wire "} out_y`,
    `);`,
    ``,
    `  assign out_y = in_a & in_b;`,
    ``,
    `endmodule`,
    ``,
  ].join("\n");
}

// ---- Explanations ----

function explainCounter(opts: Record<string, unknown>): ExplanationDoc {
  return {
    purpose: "A parameterized binary counter.",
    configuration: [
      `Width: ${opts.width ?? 8} bits`,
      `Direction: ${opts.direction ?? "up"}`,
      `Enable: ${opts.enable === false ? "no" : "yes"}`,
      `Wrap: ${opts.wrap ?? "overflow"}`,
      `Reset (${opts.reset_style ?? "sync"}, ${opts.reset_polarity ?? "active_low"}) value: ${opts.reset_value ?? 0}`,
      `Language: ${opts.language ?? "sv"}`,
    ],
    signals: [
      { name: "clk", direction: "input", description: "Clock." },
      { name: rstName(opts), direction: "input", description: "Reset." },
      ...(opts.enable === false
        ? []
        : [{ name: "en", direction: "input", description: "Count enable." }]),
      { name: "count_o", direction: "output", description: "Current count value." },
    ],
    reset_behavior: `On ${opts.reset_style ?? "sync"} reset the counter loads ${opts.reset_value ?? 0}.`,
    enable_behavior:
      opts.enable === false ? null : "When en is low the count holds its value.",
    assumptions: ["Single clock domain.", "Reset asserted for at least one clock."],
    limitations: [
      opts.wrap === "saturate"
        ? "Saturation logic adds a comparator on the critical path."
        : "Counter wraps modulo 2^width on overflow.",
    ],
  };
}

function explainFsm(opts: Record<string, unknown>): ExplanationDoc {
  const states = (opts.states as string[] | undefined) ?? [];
  return {
    purpose: `A ${opts.machine ?? "moore"} finite state machine skeleton.`,
    configuration: [
      `States: ${states.join(", ")}`,
      `Encoding: ${opts.encoding ?? "binary"}`,
      `Machine type: ${opts.machine ?? "moore"}`,
      `Reset state: ${opts.reset_state ?? states[0] ?? "?"}`,
      `Outputs: ${(opts.outputs as string[] | undefined)?.join(", ") || "(none)"}`,
    ],
    signals: [
      { name: "clk", direction: "input", description: "Clock." },
      { name: rstName(opts), direction: "input", description: "Reset." },
      ...(((opts.outputs as string[] | undefined) ?? []).map((o) => ({
        name: o,
        direction: "output",
        description: `FSM output ${o}.`,
      }))),
    ],
    reset_behavior: `On reset the machine enters '${opts.reset_state ?? states[0] ?? "?"}'.`,
    enable_behavior: null,
    assumptions: ["Transition logic is a skeleton and must be completed by the user."],
    limitations: [
      "Output and transition logic contain TODO markers; not synthesizable as-is.",
    ],
  };
}

function explainGeneric(name: string, opts: Record<string, unknown>): ExplanationDoc {
  return {
    purpose: `${name} (representative mock explanation).`,
    configuration: Object.entries(opts).map(([k, v]) => `${k}: ${JSON.stringify(v)}`),
    signals: [
      { name: "in_a", direction: "input", description: "First input." },
      { name: "in_b", direction: "input", description: "Second input." },
      { name: "out_y", direction: "output", description: "Result." },
    ],
    reset_behavior: "No reset (combinational) in this mock.",
    enable_behavior: null,
    assumptions: ["Mock output for UI development only."],
    limitations: ["Not the real generator; wire to WP-06 for production RTL."],
  };
}

/** Deterministic lint status driven by the config so badges are stable. */
function mockLint(snippetId: string, opts: Record<string, unknown>): LintReport {
  // CDC width>1 -> warnings; fsm -> warnings (TODO skeleton); else clean.
  if (snippetId === "cdc-synchronizer" && Number(opts.width ?? 1) > 1) {
    return {
      status: "warnings",
      messages: [
        {
          severity: "WARNING",
          code: "MULTIDRIVEN",
          line: 12,
          text: "Multi-bit CDC is only safe for gray-coded or quasi-static signals.",
        },
      ],
    };
  }
  if (snippetId === "fsm") {
    return {
      status: "warnings",
      messages: [
        {
          severity: "WARNING",
          code: "UNUSED",
          line: 1,
          text: "Signal is unused: transition logic is a user-completed skeleton.",
        },
      ],
    };
  }
  if (snippetId === "demux") {
    // Demonstrate the 'unavailable' badge state in the mock catalog.
    return { status: "unavailable", messages: [] };
  }
  return { status: "clean", messages: [] };
}

export async function mockGenerate(
  snippetId: string,
  options: Record<string, unknown>,
): Promise<GenerateResponse> {
  const entry = getEntry(snippetId); // throws MockNotFoundError

  // Per-field + cross-field validation -> 422.
  const errors: ValidationErrorItem[] = [];
  const props = entry.json_schema.properties ?? {};
  for (const [name, sub] of Object.entries(props)) {
    validateField(name, sub, entry.json_schema, options[name], errors);
  }
  crossFieldValidate(snippetId, options, errors);
  if (errors.length > 0) throw new MockValidationError(errors);

  const language = options.language === "verilog" ? "verilog" : "sv";
  const hash = await configHash(snippetId, options);
  const fragment = options.include_wrapper === false;

  let body: string;
  let explanation: ExplanationDoc;
  if (snippetId === "counter") {
    body = emitCounter(options);
    explanation = explainCounter(options);
  } else if (snippetId === "fsm") {
    body = emitFsm(options);
    explanation = explainFsm(options);
  } else {
    body = emitGeneric(snippetId, entry.name, options);
    explanation = explainGeneric(entry.name, options);
  }

  const moduleName = snippetId.replace(/-/g, "_");
  const filename = `${moduleName}${fragment ? "_fragment" : ""}.${ext(language)}`;
  const code = HEADER(entry.name, hash, language) + body;

  return {
    code,
    filename,
    language,
    explanation,
    lint: mockLint(snippetId, options),
    config_hash: hash,
  };
}

// ---------------------------------------------------------------------------
// v2 mock: multi-file generation. Snippets wrap the v1 output in a single rtl
// file; module-kind items (edge-detector) emit rtl + doc files. Lint is a LIST
// with one entry per rtl file, matching the backend v2 contract.
// ---------------------------------------------------------------------------

function getV2Entry(itemId: string) {
  const entry = mockCatalogV2.items.find((i) => i.id === itemId);
  if (!entry) throw new MockNotFoundError(itemId);
  return entry;
}

/** Doc file (markdown) for a module, including the contract's port table. */
function emitEdgeDetectorDoc(
  name: string,
  hash: string,
  opts: Record<string, unknown>,
): string {
  const rst = rstName(opts);
  const width = Number(opts.width ?? 1);
  const busSuffix = width > 1 ? ` [${width - 1}:0]` : "";
  return [
    `# ${name}`,
    ``,
    `_SemiCraft (mock) — config_hash: ${hash}_`,
    ``,
    `Detects ${opts.edge ?? "rising"} edges on a ${width}-bit input and emits a`,
    `one-cycle pulse per detected edge.`,
    ``,
    `## Ports`,
    ``,
    `| Port | Direction | Description |`,
    `| ---- | --------- | ----------- |`,
    `| clk | input | Clock. |`,
    `| ${rst} | input | Reset. |`,
    `| d${busSuffix} | input | Signal under observation. |`,
    `| edge_o${busSuffix} | output | One-cycle edge pulse. |`,
    ``,
  ].join("\n");
}

function emitEdgeDetector(opts: Record<string, unknown>): string {
  const sv = opts.language !== "verilog";
  const rst = rstName(opts);
  const width = Number(opts.width ?? 1);
  const bus = width > 1 ? `[WIDTH-1:0] ` : "";
  const detect =
    opts.edge === "falling"
      ? "d_prev & ~d"
      : opts.edge === "both"
        ? "d ^ d_prev"
        : "d & ~d_prev";
  return [
    `module edge_detector #(`,
    `  parameter int WIDTH = ${width}`,
    `) (`,
    `  input  wire ${rst === "rst_n" ? "" : ""}      clk,`,
    `  input  wire       ${rst},`,
    `  input  wire ${bus}d,`,
    `  output ${sv ? "logic" : "reg  "} ${bus}edge_o`,
    `);`,
    ``,
    `  ${sv ? "logic" : "reg  "} ${bus}d_prev;`,
    ``,
    `  ${sv ? "always_ff" : "always"} @(posedge clk) begin`,
    `    if (${opts.reset_polarity === "active_high" ? rst : `!${rst}`}) d_prev <= '0;`,
    `    else d_prev <= d;`,
    `  end`,
    ``,
    `  assign edge_o = ${detect};`,
    ``,
    `endmodule`,
    ``,
  ].join("\n");
}

function explainEdgeDetector(opts: Record<string, unknown>): ExplanationDoc {
  return {
    purpose: `A clocked ${opts.edge ?? "rising"}-edge detector.`,
    configuration: [
      `Width: ${opts.width ?? 1} bit(s)`,
      `Edge: ${opts.edge ?? "rising"}`,
      `Reset (${opts.reset_style ?? "sync"}, ${opts.reset_polarity ?? "active_low"})`,
      `Language: ${opts.language ?? "sv"}`,
    ],
    signals: [
      { name: "clk", direction: "input", description: "Clock." },
      { name: rstName(opts), direction: "input", description: "Reset." },
      { name: "d", direction: "input", description: "Signal under observation." },
      { name: "edge_o", direction: "output", description: "One-cycle edge pulse." },
    ],
    reset_behavior: "On reset the delayed sample clears to zero.",
    enable_behavior: null,
    assumptions: ["Single clock domain.", "Input is synchronous to clk."],
    limitations: ["Multi-bit detection is per-bit, not a bus-level event."],
  };
}

export async function mockGenerateV2(
  itemId: string,
  options: Record<string, unknown>,
): Promise<GenerateV2Response> {
  const entry = getV2Entry(itemId); // throws MockNotFoundError

  // Per-field + cross-field validation -> 422 (same path as v1).
  const errors: ValidationErrorItem[] = [];
  const props = entry.json_schema.properties ?? {};
  for (const [name, sub] of Object.entries(props)) {
    validateField(name, sub, entry.json_schema, options[name], errors);
  }
  crossFieldValidate(itemId, options, errors);
  if (errors.length > 0) throw new MockValidationError(errors);

  const language = options.language === "verilog" ? "verilog" : "sv";
  const hash = await configHash(itemId, options);
  const files: GeneratedFile[] = [];

  if (entry.kind === "module" && itemId === "edge-detector") {
    const rtlPath = `edge_detector.${ext(language)}`;
    files.push({
      path: rtlPath,
      kind: "rtl",
      text: HEADER(entry.name, hash, language) + emitEdgeDetector(options),
    });
    files.push({
      path: "edge_detector.md",
      kind: "doc",
      text: emitEdgeDetectorDoc(entry.name, hash, options),
    });
    const lint: LintFileReport[] = [
      { path: rtlPath, ...mockLint(itemId, options) },
    ];
    return {
      files,
      explanation: explainEdgeDetector(options),
      lint,
      config_hash: hash,
      language,
    };
  }

  // Snippet-kind: single rtl file wrapping the v1 output.
  const v1 = await mockGenerate(itemId, options);
  files.push({ path: v1.filename, kind: "rtl", text: v1.code });
  return {
    files,
    explanation: v1.explanation,
    lint: [{ path: v1.filename, ...v1.lint }],
    config_hash: v1.config_hash,
    language: v1.language,
  };
}

/** Mock of POST /api/v2/generate/zip — returns a synthetic zip-like blob. */
export async function mockZip(
  itemId: string,
  options: Record<string, unknown>,
): Promise<ZipDownload> {
  const data = await mockGenerateV2(itemId, options);
  // Not a real zip archive (the mock layer is for UI dev only); callers that
  // need byte-faithful zips point NEXT_PUBLIC_API_BASE at the backend.
  const payload = data.files.map((f) => `=== ${f.path} ===\n${f.text}`).join("\n\n");
  return {
    blob: new Blob([payload], { type: "application/zip" }),
    filename: `semicraft_${itemId}_${data.config_hash}.zip`,
  };
}

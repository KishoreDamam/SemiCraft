import { describe, expect, it } from "vitest";
import { describeField, describeSchema } from "@/lib/schema";
import type {
  CatalogResponse,
  JsonSchema,
  SnippetCatalogEntry,
} from "@/lib/types";
import realCatalog from "@/tests/fixtures/real-catalog.json";

/**
 * Integration-of-contract tests: feed the REAL Pydantic v2 `model_json_schema()`
 * output (captured from GET /api/v1/snippets into fixtures/real-catalog.json)
 * through the schema interpreter and assert every snippet produces a sensible
 * widget list. This is the guard against the mock schemas having diverged from
 * what Pydantic actually emits (inline enums vs $defs/allOf, nested $ref
 * sub-models, anyOf Optional encoding, array bounds, etc.).
 */

const catalog = realCatalog as unknown as CatalogResponse;

function entry(id: string): SnippetCatalogEntry {
  const e = catalog.snippets.find((s) => s.id === id);
  if (!e) throw new Error(`snippet ${id} missing from real catalog`);
  return e;
}

/** All property keys on the raw schema (rendered or skipped). */
function propKeys(schema: JsonSchema): string[] {
  return Object.keys(schema.properties ?? {});
}

describe("real catalog fixture", () => {
  it("contains all 10 registered snippets", () => {
    expect(catalog.snippets).toHaveLength(10);
    const ids = catalog.snippets.map((s) => s.id).sort();
    expect(ids).toEqual(
      [
        "cdc-synchronizer",
        "comparator",
        "counter",
        "decoder",
        "demux",
        "encoder",
        "fsm",
        "mux",
        "register",
        "shift-register",
      ].sort(),
    );
  });
});

describe("real schema interpretation — every snippet", () => {
  for (const snippet of catalog.snippets) {
    describe(snippet.id, () => {
      const schema = snippet.json_schema as JsonSchema;
      const descriptors = describeSchema(schema);
      const byName = new Map(descriptors.map((d) => [d.name, d]));

      it("produces a non-empty widget list", () => {
        expect(descriptors.length).toBeGreaterThan(0);
      });

      it("gives every non-nested property a real widget kind", () => {
        // Every rendered descriptor must have one of the known widget kinds;
        // in particular none should silently fall through to a bogus state.
        const known = new Set([
          "segmented",
          "dropdown",
          "toggle",
          "number",
          "chips",
          "text",
        ]);
        for (const d of descriptors) {
          expect(known.has(d.kind)).toBe(true);
        }
      });

      it("covers every property (rendered, or a skipped nested object)", () => {
        // Each schema property must be accounted for: it either renders as a
        // widget, or it is a nested object (Pydantic sub-model) intentionally
        // skipped by the flat form. Nothing may be dropped for other reasons.
        for (const name of propKeys(schema)) {
          if (byName.has(name)) continue;
          const raw = schema.properties![name];
          const d = describeField(name, raw, schema);
          expect(d.kind).toBe("nested");
        }
      });

      it("carries a non-empty description on every rendered field", () => {
        for (const d of descriptors) {
          expect(typeof d.description).toBe("string");
          expect((d.description ?? "").length).toBeGreaterThan(0);
        }
      });

      it("carries a schema default through for every non-array field", () => {
        // Scalar/enum/bool fields carry their default on the property schema.
        // Array fields (chips) don't always: Pydantic omits `default` from the
        // property schema for list fields with a default_factory-style default,
        // so their default is only guaranteed via the `defaults` payload (see
        // the separate check below). That's correct Pydantic behaviour, not a bug.
        for (const d of descriptors) {
          if (d.kind === "chips") continue;
          expect(d.default).not.toBeUndefined();
        }
      });

      it("the snippet `defaults` payload covers every rendered field", () => {
        // The form seeds values from `defaults`, so every rendered widget must
        // have a starting value there — including chips fields.
        for (const d of descriptors) {
          expect(Object.prototype.hasOwnProperty.call(snippet.defaults, d.name)).toBe(
            true,
          );
        }
      });

      it("resolves enum widgets to concrete options", () => {
        for (const d of descriptors) {
          if (d.kind === "segmented" || d.kind === "dropdown") {
            expect(d.options && d.options.length).toBeGreaterThan(0);
          }
        }
      });

      it("gives integer widgets at least a lower bound", () => {
        for (const d of descriptors) {
          if (d.kind === "number") {
            expect(d.integer).toBe(true);
            // Every numeric option in these snippets has at least a minimum.
            expect(typeof d.min).toBe("number");
          }
        }
      });
    });
  }
});

describe("real schema — specific known shapes", () => {
  it("counter: inline string enum -> segmented; bounded int -> number", () => {
    const map = new Map(
      describeSchema(entry("counter").json_schema as JsonSchema).map((d) => [
        d.name,
        d,
      ]),
    );
    const reset = map.get("reset_style")!;
    expect(reset.kind).toBe("segmented");
    expect(reset.options?.map((o) => o.value)).toEqual(["sync", "async"]);

    const width = map.get("width")!;
    expect(width.kind).toBe("number");
    expect(width.min).toBe(1);
    expect(width.max).toBe(1024);
    expect(width.integer).toBe(true);

    const lang = map.get("language")!;
    expect(lang.kind).toBe("segmented");
    expect(lang.options?.map((o) => o.value)).toEqual(["sv", "verilog"]);
  });

  it("counter: nested `naming` sub-model is skipped, not rendered as text", () => {
    const schema = entry("counter").json_schema as JsonSchema;
    const names = describeSchema(schema).map((d) => d.name);
    expect(names).not.toContain("naming");
    // But it IS a real property; interpreter classifies it as nested.
    const d = describeField("naming", schema.properties!.naming, schema);
    expect(d.kind).toBe("nested");
  });

  it("fsm: states array-of-string -> chips with item bounds, no itemEnum", () => {
    const schema = entry("fsm").json_schema as JsonSchema;
    const map = new Map(describeSchema(schema).map((d) => [d.name, d]));
    const states = map.get("states")!;
    expect(states.kind).toBe("chips");
    expect(states.minItems).toBe(2);
    expect(states.maxItems).toBe(16);
    expect(states.itemEnum).toBeUndefined();
  });

  it("fsm: reset_state anyOf[string,null] -> text widget", () => {
    const schema = entry("fsm").json_schema as JsonSchema;
    const map = new Map(describeSchema(schema).map((d) => [d.name, d]));
    expect(map.get("reset_state")!.kind).toBe("text");
  });

  it("comparator: outputs array with item enum -> chips + itemEnum", () => {
    const schema = entry("comparator").json_schema as JsonSchema;
    const map = new Map(describeSchema(schema).map((d) => [d.name, d]));
    const outputs = map.get("outputs")!;
    expect(outputs.kind).toBe("chips");
    expect(outputs.itemEnum?.map((o) => o.value)).toEqual([
      "eq",
      "ne",
      "lt",
      "le",
      "gt",
      "ge",
    ]);
  });

  it("encoder: integer enum num_inputs -> segmented (3 options)", () => {
    const schema = entry("encoder").json_schema as JsonSchema;
    const map = new Map(describeSchema(schema).map((d) => [d.name, d]));
    const n = map.get("num_inputs")!;
    expect(n.kind).toBe("segmented");
    expect(n.options?.map((o) => o.value)).toEqual([4, 8, 16]);
  });

  it("decoder: integer enum num_outputs (4 options) -> segmented", () => {
    const schema = entry("decoder").json_schema as JsonSchema;
    const map = new Map(describeSchema(schema).map((d) => [d.name, d]));
    expect(map.get("num_outputs")!.kind).toBe("segmented");
  });
});

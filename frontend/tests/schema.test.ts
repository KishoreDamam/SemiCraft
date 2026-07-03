import { describe, expect, it } from "vitest";
import { describeSchema, flattenSchema } from "@/lib/schema";
import { counterSchema } from "@/mocks/schemas/counter";
import { fsmSchema } from "@/mocks/schemas/fsm";

function byName(schema = counterSchema) {
  const map = new Map(describeSchema(schema).map((d) => [d.name, d]));
  return map;
}

describe("schema interpreter — counter (inline enums)", () => {
  const fields = byName(counterSchema);

  it("maps a <=4-option string enum to a segmented control", () => {
    const d = fields.get("reset_style")!; // sync | async
    expect(d.kind).toBe("segmented");
    expect(d.options?.map((o) => o.value)).toEqual(["sync", "async"]);
  });

  it("maps direction (3 options) to segmented, language (2) to segmented", () => {
    expect(fields.get("direction")!.kind).toBe("segmented");
    expect(fields.get("language")!.kind).toBe("segmented");
  });

  it("maps booleans to toggles", () => {
    expect(fields.get("enable")!.kind).toBe("toggle");
    expect(fields.get("include_wrapper")!.kind).toBe("toggle");
  });

  it("maps a bounded integer to a number widget with min/max", () => {
    const d = fields.get("width")!;
    expect(d.kind).toBe("number");
    expect(d.min).toBe(1);
    expect(d.max).toBe(1024);
    expect(d.integer).toBe(true);
  });

  it("carries descriptions through for tooltips", () => {
    expect(fields.get("width")!.description).toMatch(/bit width/i);
  });

  it("carries defaults through", () => {
    expect(fields.get("width")!.default).toBe(8);
    expect(fields.get("enable")!.default).toBe(true);
    expect(fields.get("language")!.default).toBe("sv");
  });
});

describe("schema interpreter — fsm ($defs/$ref indirection + arrays)", () => {
  const fields = byName(fsmSchema);

  it("resolves an enum behind allOf/$ref (encoding)", () => {
    const d = fields.get("encoding")!;
    expect(d.kind).toBe("segmented");
    expect(d.options?.map((o) => o.value)).toEqual(["binary", "onehot", "gray"]);
    // description lives on the property, not the $def
    expect(d.description).toMatch(/encoding scheme/i);
  });

  it("resolves machine (2-option enum via $ref)", () => {
    const d = fields.get("machine")!;
    expect(d.kind).toBe("segmented");
    expect(d.options?.map((o) => o.value)).toEqual(["moore", "mealy"]);
  });

  it("maps array-of-string to a chips widget with item bounds", () => {
    const d = fields.get("states")!;
    expect(d.kind).toBe("chips");
    expect(d.minItems).toBe(2);
    expect(d.maxItems).toBe(16);
    expect(d.uniqueItems).toBe(true);
    expect(d.itemEnum).toBeUndefined();
  });

  it("maps reset_state (unconstrained string) to a text widget", () => {
    expect(fields.get("reset_state")!.kind).toBe("text");
  });
});

describe("flattenSchema helpers", () => {
  it("selects a dropdown for >4 enum options", () => {
    const many = {
      type: "object" as const,
      properties: {
        f: {
          type: "string" as const,
          enum: ["a", "b", "c", "d", "e"],
        },
      },
    };
    expect(describeSchema(many)[0].kind).toBe("dropdown");
  });

  it("normalises exclusive numeric bounds to inclusive", () => {
    const flat = flattenSchema(
      { type: "integer", exclusiveMinimum: 0, exclusiveMaximum: 10 },
      {},
    );
    expect(flat.exclusiveMinimum).toBe(0);
    const d = describeSchema({
      type: "object",
      properties: { n: { type: "integer", exclusiveMinimum: 0, exclusiveMaximum: 10 } },
    })[0];
    expect(d.min).toBe(1);
    expect(d.max).toBe(9);
  });

  it("detects a constrained item enum (comparator-style outputs)", () => {
    const d = describeSchema({
      type: "object",
      properties: {
        outputs: {
          type: "array",
          items: { type: "string", enum: ["eq", "lt", "gt"] },
        },
      },
    })[0];
    expect(d.kind).toBe("chips");
    expect(d.itemEnum?.map((o) => o.value)).toEqual(["eq", "lt", "gt"]);
  });
});

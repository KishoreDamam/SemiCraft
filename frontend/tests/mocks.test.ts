import { describe, expect, it } from "vitest";
import { generate, fetchCatalog, isMockMode } from "@/lib/api";
import { configHash, canonicalJson } from "@/lib/hash";
import { counterDefaults } from "@/mocks/schemas/counter";
import { fsmDefaults } from "@/mocks/schemas/fsm";

describe("mock mode + contract shapes", () => {
  it("defaults to mock mode when NEXT_PUBLIC_API_BASE is unset", () => {
    expect(isMockMode()).toBe(true);
  });

  it("catalog lists all 10 MVP snippets with schemas and defaults", async () => {
    const cat = await fetchCatalog();
    expect(cat.snippets).toHaveLength(10);
    const ids = cat.snippets.map((s) => s.id).sort();
    expect(ids).toContain("counter");
    expect(ids).toContain("fsm");
    for (const s of cat.snippets) {
      expect(s.json_schema.type).toBe("object");
      expect(s.defaults).toBeTypeOf("object");
    }
  });

  it("counter generate returns a §4-shaped 200 response", async () => {
    const res = await generate("counter", counterDefaults);
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    const d = res.data;
    expect(d.language).toBe("sv");
    expect(d.filename).toBe("counter.sv");
    expect(d.code).toContain("module counter");
    expect(d.config_hash).toMatch(/^[0-9a-f]{12}$/);
    expect(d.lint.status).toBe("clean");
    expect(d.explanation.purpose).toBeTruthy();
    expect(d.explanation.signals.length).toBeGreaterThan(0);
  });

  it("verilog target yields a .v filename", async () => {
    const res = await generate("counter", { ...counterDefaults, language: "verilog" });
    expect(res.ok).toBe(true);
    if (res.ok) expect(res.data.filename).toBe("counter.v");
  });

  it("fragment mode adds _fragment to the filename", async () => {
    const res = await generate("counter", { ...counterDefaults, include_wrapper: false });
    expect(res.ok).toBe(true);
    if (res.ok) expect(res.data.filename).toBe("counter_fragment.sv");
  });

  it("fsm generate returns warnings lint (skeleton) and a full explanation", async () => {
    const res = await generate("fsm", fsmDefaults);
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    expect(res.data.lint.status).toBe("warnings");
    expect(res.data.lint.messages.length).toBeGreaterThan(0);
    expect(res.data.code).toContain("module fsm");
    expect(res.data.explanation.configuration.length).toBeGreaterThan(0);
  });

  it("422 on out-of-range integer maps to a field error", async () => {
    const res = await generate("counter", { ...counterDefaults, width: 9999 });
    expect(res.ok).toBe(false);
    if (res.ok) return;
    expect(res.status).toBe(422);
    if (res.status === 422) {
      expect(res.fieldErrors.width).toMatch(/less than or equal to 1024/);
    }
  });

  it("422 on fsm reset_state not in states (cross-field)", async () => {
    const res = await generate("fsm", { ...fsmDefaults, reset_state: "nope" });
    expect(res.ok).toBe(false);
    if (!res.ok && res.status === 422) {
      expect(res.fieldErrors.reset_state).toMatch(/must be one of/);
    }
  });

  it("404 on unknown snippet", async () => {
    const res = await generate("does-not-exist", {});
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.status).toBe(404);
  });

  it("config_hash is deterministic and order-independent", async () => {
    const a = await configHash("counter", { width: 8, enable: true });
    const b = await configHash("counter", { enable: true, width: 8 });
    expect(a).toBe(b);
    expect(canonicalJson({ b: 1, a: 2 })).toBe('{"a":2,"b":1}');
  });
});

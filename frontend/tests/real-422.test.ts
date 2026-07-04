import { afterEach, describe, expect, it, vi } from "vitest";
import real422 from "@/tests/fixtures/real-422-counter.json";

/**
 * Verifies the frontend's real-API path parses the ACTUAL FastAPI 422 envelope
 * captured from the backend (fixtures/real-422-counter.json: counter width=0).
 * fieldErrorsFrom() is module-private, so we exercise it through generate()'s
 * real-backend branch by (a) setting NEXT_PUBLIC_API_BASE so isMockMode() is
 * false and (b) stubbing fetch to return the real 422 body. This is the guard
 * that the loc-prefix convention (["body","options",<field>]) still maps to the
 * right form field.
 */

afterEach(() => {
  vi.restoreAllMocks();
  vi.resetModules();
  vi.unstubAllEnvs();
});

async function loadApiWithRealBase() {
  vi.stubEnv("NEXT_PUBLIC_API_BASE", "http://backend.test");
  vi.resetModules();
  return await import("@/lib/api");
}

describe("real 422 envelope parsing", () => {
  it("fixture is the real FastAPI/Pydantic shape", () => {
    // Sanity-check the captured fixture matches the documented §4 shape.
    expect(Array.isArray(real422.detail)).toBe(true);
    const item = real422.detail[0];
    expect(item.loc).toEqual(["body", "options", "width"]);
    expect(typeof item.msg).toBe("string");
    expect(item.type).toBe("greater_than_equal");
  });

  it("generate() maps the real 422 to an inline field error keyed by field name", async () => {
    const api = await loadApiWithRealBase();
    expect(api.isMockMode()).toBe(false);

    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify(real422), {
          status: 422,
          headers: { "content-type": "application/json" },
        }),
      ),
    );

    const result = await api.generate("counter", { width: 0 });
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error("expected failure");
    expect(result.status).toBe(422);
    if (result.status !== 422) throw new Error("expected 422");
    // The last string segment of loc ("width") is used as the field key.
    expect(result.fieldErrors.width).toBe(
      "Input should be greater than or equal to 1",
    );
    // Only the offending field appears.
    expect(Object.keys(result.fieldErrors)).toEqual(["width"]);
  });
});

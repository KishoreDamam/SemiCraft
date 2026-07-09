import { describe, expect, it } from "vitest";
import {
  fetchZip,
  filenameFromDisposition,
  generateV2,
  getCatalog,
  isMockMode,
} from "@/lib/api";
import { counterDefaults } from "@/mocks/schemas/counter";

describe("v2 client against mocks", () => {
  it("runs in mock mode when NEXT_PUBLIC_API_BASE is unset", () => {
    expect(isMockMode()).toBe(true);
  });

  it("catalog groups items into snippets and modules by kind", async () => {
    const cat = await getCatalog();
    const kinds = new Set(cat.items.map((i) => i.kind));
    expect(kinds.has("snippet")).toBe(true);
    expect(kinds.has("module")).toBe(true);

    const counter = cat.items.find((i) => i.id === "counter")!;
    expect(counter.kind).toBe("snippet");
    expect(counter.maturity).toBe("stable");

    const edge = cat.items.find((i) => i.id === "edge-detector")!;
    expect(edge.kind).toBe("module");
    expect(edge.maturity).toBe("beta");

    // ids are unique
    const ids = cat.items.map((i) => i.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("snippet generate returns a single rtl file with a per-file lint entry", async () => {
    const res = await generateV2("counter", counterDefaults);
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    const d = res.data;
    expect(d.files).toHaveLength(1);
    expect(d.files[0].kind).toBe("rtl");
    expect(d.files[0].path).toBe("counter.sv");
    expect(d.files[0].text).toContain("module counter");
    expect(Array.isArray(d.lint)).toBe(true);
    expect(d.lint).toHaveLength(1);
    expect(d.lint[0].path).toBe("counter.sv");
    expect(d.language).toBe("sv");
    expect(d.config_hash).toMatch(/^[0-9a-f]{12}$/);
  });

  it("module generate returns rtl + doc files, lint only over rtl", async () => {
    const res = await generateV2("edge-detector", { language: "sv" });
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    const d = res.data;
    const kinds = d.files.map((f) => f.kind);
    expect(kinds).toContain("rtl");
    expect(kinds).toContain("doc");

    const rtl = d.files.find((f) => f.kind === "rtl")!;
    const doc = d.files.find((f) => f.kind === "doc")!;
    expect(rtl.text).toContain("module edge_detector");
    expect(doc.path.endsWith(".md")).toBe(true);
    expect(doc.text).toContain("| Port | Direction | Description |");

    // lint list covers rtl only, not doc
    const lintPaths = d.lint.map((l) => l.path);
    expect(lintPaths).toContain(rtl.path);
    expect(lintPaths).not.toContain(doc.path);
    expect(lintPaths).toHaveLength(1);
  });

  it("maps a 422 onto the offending field", async () => {
    const res = await generateV2("counter", { ...counterDefaults, width: 9999 });
    expect(res.ok).toBe(false);
    if (!res.ok && res.status === 422) {
      expect(res.fieldErrors.width).toMatch(/less than or equal to 1024/);
    }
  });

  it("returns 404 for an unknown item", async () => {
    const res = await generateV2("does-not-exist", {});
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.status).toBe(404);
  });

  it("fetchZip returns a blob with a content-disposition-style filename", async () => {
    const zip = await fetchZip("edge-detector", { language: "sv" });
    expect(zip.blob).toBeInstanceOf(Blob);
    expect(zip.blob.type).toBe("application/zip");
    expect(zip.filename).toMatch(/^semicraft_edge-detector_[0-9a-f]{12}\.zip$/);
  });
});

describe("filenameFromDisposition", () => {
  it("parses a plain filename", () => {
    expect(
      filenameFromDisposition('attachment; filename="semicraft_x_abc.zip"', "fb.zip"),
    ).toBe("semicraft_x_abc.zip");
  });

  it("prefers RFC 5987 filename* and decodes it", () => {
    expect(
      filenameFromDisposition("attachment; filename*=UTF-8''semi%20craft.zip", "fb.zip"),
    ).toBe("semi craft.zip");
  });

  it("falls back when the header is missing", () => {
    expect(filenameFromDisposition(null, "fallback.zip")).toBe("fallback.zip");
  });
});

import type {
  CatalogResponse,
  CatalogV2Response,
  GenerateResponse,
  GenerateResult,
  GenerateV2Response,
  GenerateV2Result,
  SimulateResponse,
  SimulateResult,
  ValidationErrorResponse,
  ZipDownload,
} from "@/lib/types";
import { mockCatalog, mockCatalogV2 } from "@/mocks/catalog";
import {
  MockNotFoundError,
  MockValidationError,
  mockGenerate,
  mockGenerateV2,
  mockSimulate,
  mockZip,
} from "@/mocks/generate";

/**
 * Single API client module. When NEXT_PUBLIC_API_BASE is unset, all calls are
 * served from the local mock layer (mocks/). When set, calls hit the real
 * backend at `${base}/api/v1/...` implementing the §4 contract.
 *
 * The env var is read via process.env so Next.js inlines it at build time.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export function isMockMode(): boolean {
  return !API_BASE;
}

function fieldErrorsFrom(body: ValidationErrorResponse): Record<string, string> {
  const out: Record<string, string> = {};
  for (const item of body.detail ?? []) {
    // loc is like ["body", "options", "<field>"] from FastAPI, or ["<field>"]
    // from our mock. Take the last string segment as the field name.
    const field = [...item.loc].reverse().find((p) => typeof p === "string");
    if (typeof field === "string" && !(field in out)) {
      out[field] = item.msg;
    }
  }
  return out;
}

export async function fetchCatalog(): Promise<CatalogResponse> {
  if (isMockMode()) {
    return mockCatalog;
  }
  const res = await fetch(`${API_BASE}/api/v1/snippets`, {
    headers: { accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to load snippet catalog (${res.status})`);
  }
  return (await res.json()) as CatalogResponse;
}

export async function generate(
  snippetId: string,
  options: Record<string, unknown>,
): Promise<GenerateResult> {
  if (isMockMode()) {
    try {
      const data = await mockGenerate(snippetId, options);
      return { ok: true, data };
    } catch (e) {
      if (e instanceof MockValidationError) {
        return {
          ok: false,
          status: 422,
          fieldErrors: fieldErrorsFrom({ detail: e.items }),
        };
      }
      if (e instanceof MockNotFoundError) {
        return { ok: false, status: 404, message: "Unknown snippet." };
      }
      return { ok: false, status: 500, message: "Generation failed." };
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1/generate`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ snippet_id: snippetId, options }),
    });
  } catch {
    return { ok: false, status: 0, message: "Network error contacting backend." };
  }

  if (res.ok) {
    return { ok: true, data: (await res.json()) as GenerateResponse };
  }
  if (res.status === 422) {
    const body = (await res.json()) as ValidationErrorResponse;
    return { ok: false, status: 422, fieldErrors: fieldErrorsFrom(body) };
  }
  if (res.status === 404) {
    return { ok: false, status: 404, message: "Unknown snippet." };
  }
  return {
    ok: false,
    status: res.status,
    message: `Generation failed (${res.status}).`,
  };
}

// ---------------------------------------------------------------------------
// API v2 (multi-file). Appendix A.1. When mock mode is on these are served from
// the mock layer; otherwise they hit `${base}/api/v2/...`.
// ---------------------------------------------------------------------------

export async function getCatalog(): Promise<CatalogV2Response> {
  if (isMockMode()) {
    return mockCatalogV2;
  }
  const res = await fetch(`${API_BASE}/api/v2/catalog`, {
    headers: { accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to load catalog (${res.status})`);
  }
  return (await res.json()) as CatalogV2Response;
}

export async function generateV2(
  itemId: string,
  options: Record<string, unknown>,
): Promise<GenerateV2Result> {
  if (isMockMode()) {
    try {
      const data = await mockGenerateV2(itemId, options);
      return { ok: true, data };
    } catch (e) {
      if (e instanceof MockValidationError) {
        return {
          ok: false,
          status: 422,
          fieldErrors: fieldErrorsFrom({ detail: e.items }),
        };
      }
      if (e instanceof MockNotFoundError) {
        return { ok: false, status: 404, message: "Unknown item." };
      }
      return { ok: false, status: 500, message: "Generation failed." };
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v2/generate`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ item_id: itemId, options }),
    });
  } catch {
    return { ok: false, status: 0, message: "Network error contacting backend." };
  }

  if (res.ok) {
    return { ok: true, data: (await res.json()) as GenerateV2Response };
  }
  if (res.status === 422) {
    const body = (await res.json()) as ValidationErrorResponse;
    return { ok: false, status: 422, fieldErrors: fieldErrorsFrom(body) };
  }
  if (res.status === 404) {
    return { ok: false, status: 404, message: "Unknown item." };
  }
  return {
    ok: false,
    status: res.status,
    message: `Generation failed (${res.status}).`,
  };
}

/**
 * Run an item's smoke testbench in the sim sandbox (POST /api/v2/simulate).
 *
 * Always resolves (never throws for "sim failed" / "verilator missing" — those
 * are `data.status` values on a 200). Non-200s (404 unknown item, 422 invalid
 * options, 5xx) come back as `{ ok: false }` so the caller can surface them.
 */
export async function simulate(
  itemId: string,
  options: Record<string, unknown>,
): Promise<SimulateResult> {
  if (isMockMode()) {
    try {
      const data = await mockSimulate(itemId, options);
      return { ok: true, data };
    } catch (e) {
      if (e instanceof MockValidationError) {
        return { ok: false, status: 422, message: "Invalid options." };
      }
      if (e instanceof MockNotFoundError) {
        return { ok: false, status: 404, message: "Unknown item." };
      }
      return { ok: false, status: 500, message: "Simulation failed." };
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v2/simulate`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ item_id: itemId, options }),
    });
  } catch {
    return { ok: false, status: 0, message: "Network error contacting backend." };
  }

  if (res.ok) {
    return { ok: true, data: (await res.json()) as SimulateResponse };
  }
  if (res.status === 422) {
    return { ok: false, status: 422, message: "Invalid options." };
  }
  if (res.status === 404) {
    return { ok: false, status: 404, message: "Unknown item." };
  }
  return { ok: false, status: res.status, message: `Simulation failed (${res.status}).` };
}

/** Extract the filename from a Content-Disposition header, with a fallback. */
export function filenameFromDisposition(
  header: string | null,
  fallback: string,
): string {
  if (!header) return fallback;
  // RFC 5987 filename*=UTF-8''... takes precedence, then the plain filename=.
  const star = /filename\*=(?:UTF-8'')?["']?([^;"']+)/i.exec(header);
  if (star) return decodeURIComponent(star[1]);
  const plain = /filename=["']?([^;"']+)/i.exec(header);
  return plain ? plain[1] : fallback;
}

/** Fetch a zip of all generated files (POST /api/v2/generate/zip). */
export async function fetchZip(
  itemId: string,
  options: Record<string, unknown>,
): Promise<ZipDownload> {
  if (isMockMode()) {
    return mockZip(itemId, options);
  }
  const res = await fetch(`${API_BASE}/api/v2/generate/zip`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/zip" },
    body: JSON.stringify({ item_id: itemId, options }),
  });
  if (!res.ok) {
    throw new Error(`Zip download failed (${res.status})`);
  }
  const blob = await res.blob();
  const filename = filenameFromDisposition(
    res.headers.get("content-disposition"),
    `semicraft_${itemId}.zip`,
  );
  return { blob, filename };
}

/** Trigger a browser "save as" for a blob under the given filename. */
export function saveBlob(blob: Blob, filename: string): void {
  if (typeof document === "undefined") return;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** Fetch the zip for an item and save it to disk. */
export async function downloadZip(
  itemId: string,
  options: Record<string, unknown>,
): Promise<void> {
  const { blob, filename } = await fetchZip(itemId, options);
  saveBlob(blob, filename);
}

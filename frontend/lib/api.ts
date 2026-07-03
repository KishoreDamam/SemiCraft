import type {
  CatalogResponse,
  GenerateResponse,
  GenerateResult,
  ValidationErrorResponse,
} from "@/lib/types";
import { mockCatalog } from "@/mocks/catalog";
import {
  MockNotFoundError,
  MockValidationError,
  mockGenerate,
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

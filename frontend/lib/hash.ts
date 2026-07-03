/**
 * Canonical JSON + config hash, matching the backend rule (§4):
 *   config_hash = sha256(snippet_id + canonical-sorted-keys JSON of options)[:12]
 *
 * Canonicalisation recursively sorts object keys so that key order in the UI
 * never changes the hash (determinism, PRD §11). Uses the Web Crypto API
 * (available in browsers and in Node >= 20 via globalThis.crypto).
 */

export function canonicalJson(value: unknown): string {
  return JSON.stringify(sortDeep(value));
}

function sortDeep(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortDeep);
  }
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const key of Object.keys(obj).sort()) {
      out[key] = sortDeep(obj[key]);
    }
    return out;
  }
  return value;
}

export async function configHash(
  snippetId: string,
  options: Record<string, unknown>,
): Promise<string> {
  const payload = snippetId + canonicalJson(options);
  const bytes = new TextEncoder().encode(payload);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hex = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, 12);
}

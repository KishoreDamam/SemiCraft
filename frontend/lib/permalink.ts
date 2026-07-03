/**
 * Permalink serialization (WP-07 task 6). The current snippet_id + options are
 * serialized into a single URL query parameter (`c`) as base64url-encoded JSON
 * and restored on load.
 *
 * base64url (RFC 4648 §5): '+'->'-', '/'->'_', padding stripped. Works in both
 * the browser and Node test environments (uses btoa/atob when present, falls
 * back to Buffer).
 */

export interface PermalinkState {
  snippet_id: string;
  options: Record<string, unknown>;
}

const PARAM = "c";

function toBase64(bytes: Uint8Array): string {
  if (typeof btoa === "function") {
    let bin = "";
    for (const b of bytes) bin += String.fromCharCode(b);
    return btoa(bin);
  }
  // Node fallback
  return Buffer.from(bytes).toString("base64");
}

function fromBase64(b64: string): Uint8Array {
  if (typeof atob === "function") {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  return new Uint8Array(Buffer.from(b64, "base64"));
}

function base64ToUrl(b64: string): string {
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function urlToBase64(u: string): string {
  const s = u.replace(/-/g, "+").replace(/_/g, "/");
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  return s + pad;
}

export function encodePermalink(state: PermalinkState): string {
  const json = JSON.stringify(state);
  const bytes = new TextEncoder().encode(json);
  return base64ToUrl(toBase64(bytes));
}

export function decodePermalink(token: string): PermalinkState | null {
  try {
    const bytes = fromBase64(urlToBase64(token));
    const json = new TextDecoder().decode(bytes);
    const parsed = JSON.parse(json) as unknown;
    if (
      parsed &&
      typeof parsed === "object" &&
      typeof (parsed as PermalinkState).snippet_id === "string" &&
      (parsed as PermalinkState).options &&
      typeof (parsed as PermalinkState).options === "object"
    ) {
      return parsed as PermalinkState;
    }
    return null;
  } catch {
    return null;
  }
}

/** Build the `?c=...` query string (without the leading '?'). */
export function toQueryString(state: PermalinkState): string {
  return `${PARAM}=${encodePermalink(state)}`;
}

/** Read + decode state from a full search string (e.g. window.location.search). */
export function fromSearch(search: string): PermalinkState | null {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const token = params.get(PARAM);
  if (!token) return null;
  return decodePermalink(token);
}

export { PARAM as PERMALINK_PARAM };

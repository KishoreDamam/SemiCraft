import { describe, expect, it } from "vitest";
import {
  decodePermalink,
  encodePermalink,
  fromSearch,
  toQueryString,
  type PermalinkState,
} from "@/lib/permalink";

const sample: PermalinkState = {
  snippet_id: "fsm",
  options: {
    states: ["idle", "run", "done"],
    encoding: "onehot",
    machine: "mealy",
    reset_state: "idle",
    width: 8,
    enable: true,
  },
};

describe("permalink round-trip", () => {
  it("encode -> decode returns the original state", () => {
    const token = encodePermalink(sample);
    const back = decodePermalink(token);
    expect(back).toEqual(sample);
  });

  it("produces base64url tokens (no +, /, or = padding)", () => {
    const token = encodePermalink(sample);
    expect(token).not.toMatch(/[+/=]/);
  });

  it("round-trips through a query string", () => {
    const qs = toQueryString(sample);
    expect(qs.startsWith("c=")).toBe(true);
    expect(fromSearch(`?${qs}`)).toEqual(sample);
    expect(fromSearch(qs)).toEqual(sample);
  });

  it("returns null for garbage / missing params", () => {
    expect(decodePermalink("!!!not-base64!!!")).toBeNull();
    expect(fromSearch("?other=1")).toBeNull();
    expect(fromSearch("")).toBeNull();
  });

  it("handles counter-style scalar options", () => {
    const counter: PermalinkState = {
      snippet_id: "counter",
      options: { width: 16, direction: "down", enable: false, reset_value: 3 },
    };
    expect(decodePermalink(encodePermalink(counter))).toEqual(counter);
  });
});

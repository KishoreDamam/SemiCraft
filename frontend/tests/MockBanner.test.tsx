/**
 * The demo-data banner (launch blocker B3).
 *
 * Through v0.4.0 `isMockMode()` existed, was correct, and was referenced
 * nowhere in the UI — only inside `lib/api.ts` and in tests. So the app knew
 * perfectly well it was serving fabricated data and never told anyone. These
 * tests pin the telling.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

async function renderBanner() {
  vi.resetModules();
  const { MockBanner } = await import("@/components/MockBanner");
  render(<MockBanner />);
}

describe("MockBanner", () => {
  const original = process.env.NEXT_PUBLIC_API_BASE;

  beforeEach(() => {
    cleanup();
  });

  afterEach(() => {
    if (original === undefined) delete process.env.NEXT_PUBLIC_API_BASE;
    else process.env.NEXT_PUBLIC_API_BASE = original;
    vi.resetModules();
  });

  it("shows in mock mode", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE;
    await renderBanner();
    expect(screen.getByTestId("mock-banner")).toBeInTheDocument();
  });

  it("says the data is not real, not merely that a backend is absent", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE;
    await renderBanner();
    const text = screen.getByTestId("mock-banner").textContent ?? "";
    // "no backend" alone reads as a connectivity hiccup. The point that has to
    // land is that what is on screen is fabricated.
    expect(text.toLowerCase()).toMatch(/demo|sample|fabricated/);
    expect(text).toMatch(/NEXT_PUBLIC_API_BASE/);
  });

  it("is announced to assistive technology", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE;
    await renderBanner();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("disappears once a real backend is configured", async () => {
    process.env.NEXT_PUBLIC_API_BASE = "http://localhost:8000";
    await renderBanner();
    expect(screen.queryByTestId("mock-banner")).toBeNull();
  });

  it("offers no way to dismiss it", async () => {
    // A dismissible warning is dismissed once and never seen again, which is
    // the silent state this banner exists to end.
    delete process.env.NEXT_PUBLIC_API_BASE;
    await renderBanner();
    const banner = screen.getByTestId("mock-banner");
    expect(banner.querySelector("button")).toBeNull();
  });
});

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GeneratorApp } from "@/components/GeneratorApp";
import { mockCatalogV2 } from "@/mocks/catalog";
import { fromSearch, type PermalinkState } from "@/lib/permalink";
import * as api from "@/lib/api";

// Stub Monaco with a <pre> that echoes the active file's text.
vi.mock("@monaco-editor/react", () => ({
  default: ({ value }: { value: string }) => <pre data-testid="code">{value}</pre>,
}));

beforeEach(() => {
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
  window.history.replaceState(null, "", "/");
});

function code() {
  return screen.getByTestId("code").textContent ?? "";
}

const edgeDefaults = mockCatalogV2.items.find((i) => i.id === "edge-detector")!.defaults;

describe("v2 module flow (edge-detector)", () => {
  it("groups the picker into Snippets and Modules with a beta badge", async () => {
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    expect(screen.getByText("Snippets")).toBeInTheDocument();
    expect(screen.getByText("Modules")).toBeInTheDocument();
    // maturity badge for edge-detector
    expect(screen.getByText("beta")).toBeInTheDocument();
  });

  it("shows a tab bar for the module and switches files (doc is markdown)", async () => {
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    // single-file snippet -> no tabs
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("option", { name: /Edge Detector/ }));
    await waitFor(() => expect(code()).toContain("module edge_detector"));

    // multi-file -> tab bar appears
    const tabs = await screen.findAllByRole("tab");
    expect(tabs).toHaveLength(2);

    // switch to the doc tab -> preview shows the markdown port table
    await userEvent.click(screen.getByRole("tab", { name: /\.md/ }));
    await waitFor(() => expect(code()).toContain("| Port | Direction | Description |"));
  });

  it("copy copies the ACTIVE tab's text", async () => {
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    await userEvent.click(screen.getByRole("option", { name: /Edge Detector/ }));
    await waitFor(() => expect(code()).toContain("module edge_detector"));

    // active = rtl by default. The label toggles Copy <-> Copied, so match both.
    await userEvent.click(screen.getByRole("button", { name: /^Cop(y|ied)$/ }));
    expect(navigator.clipboard.writeText).toHaveBeenLastCalledWith(
      expect.stringContaining("module edge_detector"),
    );

    // switch to doc tab, copy again -> doc text
    await userEvent.click(screen.getByRole("tab", { name: /\.md/ }));
    await waitFor(() => expect(code()).toContain("| Port |"));
    await userEvent.click(screen.getByRole("button", { name: /^Cop(y|ied)$/ }));
    expect(navigator.clipboard.writeText).toHaveBeenLastCalledWith(
      expect.stringContaining("| Port | Direction | Description |"),
    );
  });

  it("multi-file shows a Download .zip button that calls the zip endpoint", async () => {
    const spy = vi.spyOn(api, "downloadZip").mockResolvedValue(undefined);
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    // snippet is single-file -> plain Download, no zip button
    expect(screen.queryByRole("button", { name: "Download .zip" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("option", { name: /Edge Detector/ }));
    await waitFor(() => expect(code()).toContain("module edge_detector"));

    const zipBtn = await screen.findByRole("button", { name: "Download .zip" });
    await userEvent.click(zipBtn);
    expect(spy).toHaveBeenCalledWith("edge-detector", expect.any(Object));
    spy.mockRestore();
  });

  it("round-trips the module item_id through the permalink", async () => {
    const initial: PermalinkState = {
      snippet_id: "edge-detector",
      options: { ...edgeDefaults, edge: "both" },
    };
    render(<GeneratorApp catalog={mockCatalogV2} initialState={initial} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module edge_detector"));

    await waitFor(() => expect(window.location.search).toContain("c="));
    const restored = fromSearch(window.location.search);
    expect(restored?.snippet_id).toBe("edge-detector");
    expect(restored?.options.edge).toBe("both");
  });
});

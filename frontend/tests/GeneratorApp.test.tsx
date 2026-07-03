import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GeneratorApp } from "@/components/GeneratorApp";
import { mockCatalog } from "@/mocks/catalog";
import type { PermalinkState } from "@/lib/permalink";

// Monaco needs the DOM/canvas APIs jsdom lacks; stub it with a <pre> that
// shows the code so the generate flow is still observable.
vi.mock("@monaco-editor/react", () => ({
  default: ({ value }: { value: string }) => (
    <pre data-testid="code">{value}</pre>
  ),
}));

// clipboard for copy/share buttons
beforeEach(() => {
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
  window.history.replaceState(null, "", "/");
});

function code() {
  return screen.getByTestId("code").textContent ?? "";
}

describe("generate flow against mocks", () => {
  it("generates the default counter on mount", async () => {
    render(<GeneratorApp catalog={mockCatalog} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    // lint badge for clean counter
    expect(screen.getByText(/Lint clean/)).toBeInTheDocument();
    // explanation panel present
    expect(screen.getByText("Explanation")).toBeInTheDocument();
    expect(screen.getByText("Purpose")).toBeInTheDocument();
  });

  it("updates the preview when an option changes (debounced)", async () => {
    render(<GeneratorApp catalog={mockCatalog} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    await waitFor(() => expect(code()).toContain("WIDTH = 8"));

    const width = screen.getByLabelText("Width");
    await userEvent.clear(width);
    await userEvent.type(width, "12");
    await waitFor(() => expect(code()).toContain("WIDTH = 12"));
  });

  it("maps a 422 onto the offending field inline", async () => {
    render(<GeneratorApp catalog={mockCatalog} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));

    const width = screen.getByLabelText("Width");
    await userEvent.clear(width);
    await userEvent.type(width, "5000"); // > max 1024
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/less than or equal to 1024/),
    );
  });

  it("switches snippets and shows fsm widgets + warnings badge", async () => {
    render(<GeneratorApp catalog={mockCatalog} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));

    await userEvent.click(screen.getByRole("option", { name: /FSM Template/ }));
    await waitFor(() => expect(code()).toContain("module fsm"));
    // chips widget for states
    expect(screen.getByLabelText("Remove idle")).toBeInTheDocument();
    // warnings badge (expandable)
    expect(screen.getByRole("button", { name: /lint warning/ })).toBeInTheDocument();
  });

  it("restores state from an initial permalink", async () => {
    const initial: PermalinkState = {
      snippet_id: "counter",
      options: { ...mockCatalog.snippets[0].defaults, width: 24, direction: "down" },
    };
    render(<GeneratorApp catalog={mockCatalog} initialState={initial} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("WIDTH = 24"));
    expect(screen.getByLabelText("Width")).toHaveValue(24);
    const dir = screen.getByRole("radiogroup", { name: "Direction" });
    expect(within(dir).getByRole("radio", { name: "down" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("copy button writes the generated code to the clipboard", async () => {
    render(<GeneratorApp catalog={mockCatalog} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    await userEvent.click(screen.getByRole("button", { name: "Copy" }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining("module counter"),
    );
  });

  it("writes the permalink into the URL as it changes", async () => {
    render(<GeneratorApp catalog={mockCatalog} debounceMs={0} />);
    await waitFor(() => expect(window.location.search).toContain("c="));
  });
});

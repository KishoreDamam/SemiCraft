import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GeneratorApp } from "@/components/GeneratorApp";
import { mockCatalogV2 } from "@/mocks/catalog";
import * as api from "@/lib/api";
import type { SimulateResponse } from "@/lib/types";

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

const passResult: SimulateResponse = {
  status: "pass",
  exit_code: 0,
  stdout_tail: "driving vectors\nSMOKE PASS: edge_detector",
  stderr_tail: "",
  duration_s: 1.23,
  marker_seen: true,
};

describe("Run smoke sim button + log viewer", () => {
  it("clicking Run smoke sim calls the simulate client with the current item", async () => {
    const spy = vi.spyOn(api, "simulate").mockResolvedValue({ ok: true, data: passResult });
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));

    await userEvent.click(screen.getByRole("button", { name: /Run smoke sim/ }));
    expect(spy).toHaveBeenCalledWith("counter", expect.any(Object));
    spy.mockRestore();
  });

  it("renders the pass state with the SMOKE PASS marker and stdout tail", async () => {
    vi.spyOn(api, "simulate").mockResolvedValue({ ok: true, data: passResult });
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));

    await userEvent.click(screen.getByRole("button", { name: /Run smoke sim/ }));
    await screen.findByText(/Sim pass/);
    expect(screen.getByText(/SMOKE PASS: edge_detector/)).toBeInTheDocument();
    expect(screen.getByText(/exit 0/)).toBeInTheDocument();
  });

  it("renders the fail state red with the stderr tail", async () => {
    vi.spyOn(api, "simulate").mockResolvedValue({
      ok: true,
      data: {
        status: "fail",
        exit_code: 1,
        stdout_tail: "check mismatch at cycle 3",
        stderr_tail: "%Fatal: assertion failed",
        duration_s: 0.9,
        marker_seen: false,
      },
    });
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));

    await userEvent.click(screen.getByRole("button", { name: /Run smoke sim/ }));
    await screen.findByText(/Sim fail/);
    expect(screen.getByText(/%Fatal: assertion failed/)).toBeInTheDocument();
  });

  it("renders the unavailable state (no verilator) as a grey badge", async () => {
    vi.spyOn(api, "simulate").mockResolvedValue({
      ok: true,
      data: {
        status: "unavailable",
        exit_code: null,
        stdout_tail: "",
        stderr_tail: "verilator binary not found on PATH; sim run skipped.",
        duration_s: 0,
        marker_seen: false,
      },
    });
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));

    await userEvent.click(screen.getByRole("button", { name: /Run smoke sim/ }));
    await screen.findByText(/Sim unavailable/);
    // no exit code shown when exit_code is null
    expect(screen.queryByText(/exit/)).not.toBeInTheDocument();
  });

  it("shows no sim panel until a run happens", async () => {
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() => expect(code()).toContain("module counter"));
    expect(screen.queryByLabelText("Smoke sim result")).not.toBeInTheDocument();
  });
});

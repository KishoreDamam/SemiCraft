import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LintBadge } from "@/components/LintBadge";
import type { LintFileReport, LintReport } from "@/lib/types";

describe("LintBadge — v1 single-object shape", () => {
  it("shows a clean badge", () => {
    const lint: LintReport = { status: "clean", messages: [] };
    render(<LintBadge lint={lint} />);
    expect(screen.getByText(/Lint clean/)).toBeInTheDocument();
  });

  it("shows an expandable warnings badge", async () => {
    const lint: LintReport = {
      status: "warnings",
      messages: [{ severity: "WARNING", code: "UNUSED", line: 3, text: "unused signal" }],
    };
    render(<LintBadge lint={lint} />);
    const btn = screen.getByRole("button", { name: /1 lint warning/ });
    await userEvent.click(btn);
    expect(screen.getByText(/unused signal/)).toBeInTheDocument();
  });
});

describe("LintBadge — v2 list shape aggregation", () => {
  it("shows clean when every rtl file is clean", () => {
    const lint: LintFileReport[] = [
      { path: "a.sv", status: "clean", messages: [] },
      { path: "b.sv", status: "clean", messages: [] },
    ];
    render(<LintBadge lint={lint} />);
    expect(screen.getByText(/Lint clean/)).toBeInTheDocument();
  });

  it("aggregates to warnings (worst status) and sums message counts", async () => {
    const lint: LintFileReport[] = [
      { path: "a.sv", status: "clean", messages: [] },
      {
        path: "b.sv",
        status: "warnings",
        messages: [
          { severity: "WARNING", code: "W1", line: 1, text: "first" },
          { severity: "WARNING", code: "W2", line: 2, text: "second" },
        ],
      },
    ];
    render(<LintBadge lint={lint} />);
    const btn = screen.getByRole("button", { name: /2 lint warnings/ });
    await userEvent.click(btn);
    // per-file grouping shows the offending file path
    expect(screen.getByText("b.sv")).toBeInTheDocument();
    expect(screen.getByText(/first/)).toBeInTheDocument();
    expect(screen.getByText(/second/)).toBeInTheDocument();
  });

  it("aggregates to unavailable when no warnings but some unavailable", () => {
    const lint: LintFileReport[] = [
      { path: "a.sv", status: "clean", messages: [] },
      { path: "b.sv", status: "unavailable", messages: [] },
    ];
    render(<LintBadge lint={lint} />);
    expect(screen.getByText(/Lint unavailable/)).toBeInTheDocument();
  });

  it("warnings outrank unavailable in the aggregate", () => {
    const lint: LintFileReport[] = [
      { path: "a.sv", status: "unavailable", messages: [] },
      {
        path: "b.sv",
        status: "warnings",
        messages: [{ severity: "WARNING", code: "W1", line: 1, text: "x" }],
      },
    ];
    render(<LintBadge lint={lint} />);
    expect(screen.getByRole("button", { name: /1 lint warning/ })).toBeInTheDocument();
  });

  it("renders the placeholder for null/empty lint", () => {
    const { rerender } = render(<LintBadge lint={null} />);
    expect(screen.getByText("Lint —")).toBeInTheDocument();
    rerender(<LintBadge lint={[]} />);
    expect(screen.getByText("Lint —")).toBeInTheDocument();
  });
});

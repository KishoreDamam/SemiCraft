import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileTabs } from "@/components/FileTabs";
import type { GeneratedFile } from "@/lib/types";

const multi: GeneratedFile[] = [
  { path: "edge_detector.sv", kind: "rtl", text: "module edge_detector" },
  { path: "edge_detector.md", kind: "doc", text: "# Edge Detector" },
];

describe("FileTabs", () => {
  it("renders no tab bar for a single file", () => {
    const single: GeneratedFile[] = [
      { path: "counter.sv", kind: "rtl", text: "module counter" },
    ];
    const { container } = render(
      <FileTabs files={single} activeIndex={0} onSelect={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("renders a tab per file with the path label", () => {
    render(<FileTabs files={multi} activeIndex={0} onSelect={() => {}} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(2);
    expect(screen.getByRole("tab", { name: /edge_detector\.sv/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /edge_detector\.md/ })).toBeInTheDocument();
  });

  it("marks the active tab and calls onSelect on click", async () => {
    const onSelect = vi.fn();
    render(<FileTabs files={multi} activeIndex={0} onSelect={onSelect} />);
    const rtlTab = screen.getByRole("tab", { name: /edge_detector\.sv/ });
    const docTab = screen.getByRole("tab", { name: /edge_detector\.md/ });
    expect(rtlTab).toHaveAttribute("aria-selected", "true");
    expect(docTab).toHaveAttribute("aria-selected", "false");

    await userEvent.click(docTab);
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});

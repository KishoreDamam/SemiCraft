import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

// Model Monaco that never finishes loading (a blocked or slow network): the
// real Editor renders its `loading` node until the loader resolves.
const init = vi.fn();
vi.mock("@monaco-editor/react", () => ({
  default: ({ loading }: { loading: ReactNode }) => <>{loading}</>,
  loader: { config: vi.fn(), init: () => init() },
}));

import { CodePreview } from "@/components/CodePreview";

describe("CodePreview without Monaco", () => {
  it("shows the code as plain text while the editor loads", () => {
    init.mockReturnValue(new Promise(() => {}));
    render(<CodePreview code="module counter;" language="sv" />);
    expect(screen.getByTestId("code-plain")).toHaveTextContent("module counter;");
  });

  it("keeps showing the code when the editor fails to load", async () => {
    init.mockReturnValue(Promise.reject(new Error("blocked")));
    render(<CodePreview code="module counter;" language="sv" />);
    await waitFor(() =>
      expect(screen.getByTestId("code-plain")).toHaveTextContent("module counter;"),
    );
  });
});

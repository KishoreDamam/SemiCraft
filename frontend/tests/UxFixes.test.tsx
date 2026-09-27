import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { DynamicForm, type OptionValues } from "@/components/DynamicForm";
import { CatalogPicker } from "@/components/CatalogPicker";
import { GeneratorApp } from "@/components/GeneratorApp";
import { describeField, labelFor, sentenceCase } from "@/lib/schema";
import { mockCatalogV2 } from "@/mocks/catalog";
import type { CatalogResponse, CatalogV2Response, JsonSchema } from "@/lib/types";
import realCatalog from "@/tests/fixtures/real-catalog.json";

vi.mock("@monaco-editor/react", () => ({
  default: ({ value }: { value: string }) => <pre data-testid="code">{value}</pre>,
  loader: { config: vi.fn(), init: () => new Promise(() => {}) },
}));

beforeEach(() => {
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
  window.history.replaceState(null, "", "/");
});

function Harness({
  schema,
  initial,
  onChangeSpy,
}: {
  schema: JsonSchema;
  initial: OptionValues;
  onChangeSpy?: (name: string, value: unknown) => void;
}) {
  const [values, setValues] = useState<OptionValues>(initial);
  return (
    <DynamicForm
      schema={schema}
      values={values}
      errors={{}}
      onChange={(name, value) => {
        onChangeSpy?.(name, value);
        setValues((p) => ({ ...p, [name]: value }));
      }}
    />
  );
}

const realCounter = (realCatalog as unknown as CatalogResponse).snippets.find(
  (s) => s.id === "counter",
)!;

describe("naming style (nested sub-model) is editable", () => {
  it("renders a Naming fieldset and submits the whole merged object", async () => {
    const spy = vi.fn();
    render(
      <Harness
        schema={realCounter.json_schema as JsonSchema}
        initial={realCounter.defaults}
        onChangeSpy={spy}
      />,
    );
    const group = screen.getByRole("group", { name: "Naming" });
    await userEvent.click(within(group).getByRole("radio", { name: "camelCase" }));
    expect(spy).toHaveBeenLastCalledWith("naming", {
      convention: "camel",
      prefix: "",
      suffix: "",
    });
    await userEvent.type(within(group).getByLabelText("Prefix"), "u_");
    expect(spy).toHaveBeenLastCalledWith("naming", {
      convention: "camel",
      prefix: "u_",
      suffix: "",
    });
  });
});

describe("nullable text", () => {
  const schema: JsonSchema = {
    type: "object",
    properties: {
      reset_state: {
        anyOf: [{ type: "string" }, { type: "null" }],
        default: null,
        title: "Reset State",
        description: "State entered on reset.",
      },
    },
  };

  it("shows null as an empty box, and clearing submits null not ''", async () => {
    const spy = vi.fn();
    render(<Harness schema={schema} initial={{ reset_state: null }} onChangeSpy={spy} />);
    const box = screen.getByLabelText("Reset state");
    expect(box).toHaveValue("");
    expect(box).toHaveAttribute("placeholder", "(default)");
    await userEvent.type(box, "x");
    expect(spy).toHaveBeenLastCalledWith("reset_state", "x");
    await userEvent.clear(box);
    expect(spy).toHaveBeenLastCalledWith("reset_state", null);
  });
});

describe("enum value labels", () => {
  it("humanises terse identifiers but leaves numbers alone", () => {
    expect(labelFor("sv")).toBe("SystemVerilog");
    expect(labelFor("active_low")).toBe("Active-low");
    expect(labelFor("simple_dual")).toBe("Simple dual-port");
    expect(labelFor("rising")).toBe("Rising");
    expect(labelFor("some_new_value")).toBe("Some new value");
    expect(labelFor(16)).toBe("16");
  });
});

describe("field labels", () => {
  it("are sentence case, with Pydantic's abbreviations spelled out", () => {
    expect(sentenceCase("Include Wrapper")).toBe("Include wrapper");
    expect(sentenceCase("Num Irq")).toBe("Number of IRQ");
    expect(sentenceCase("Cpha")).toBe("CPHA");
    expect(sentenceCase("Irq Regs")).toBe("IRQ registers");
    expect(sentenceCase("Impl")).toBe("Implementation");
    expect(sentenceCase("Data Width")).toBe("Data width");
  });
});

describe("pattern-constrained strings", () => {
  it("reads a plain ^(a|b)$ alternation as an enum, not free text", () => {
    const d = describeField(
      "reset_style",
      { type: "string", pattern: "^(sync|async)$", default: "sync" },
      {},
    );
    expect(d.kind).toBe("segmented");
    expect(d.options?.map((o) => o.value)).toEqual(["sync", "async"]);
  });

  it("leaves any richer pattern as text", () => {
    const d = describeField("name", { type: "string", pattern: "^[a-z_]+$" }, {});
    expect(d.kind).toBe("text");
  });
});

describe("catalog picker", () => {
  it("filters by name and description, and says when nothing matches", async () => {
    render(
      <CatalogPicker items={mockCatalogV2.items} selectedId="counter" onSelect={() => {}} />,
    );
    const filter = screen.getByRole("searchbox", { name: "Filter catalog" });
    await userEvent.type(filter, "edge");
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual([
      expect.stringContaining("Edge Detector"),
    ]);
    await userEvent.clear(filter);
    await userEvent.type(filter, "zzz");
    expect(screen.queryAllByRole("option")).toHaveLength(0);
    expect(screen.getByText(/No items match/)).toBeInTheDocument();
  });
});

describe("first visit", () => {
  it("opens on Counter even when an IP sorts first in the catalog", async () => {
    const ipFirst: CatalogV2Response = {
      ...mockCatalogV2,
      items: [
        { ...mockCatalogV2.items.find((i) => i.id === "edge-detector")!, id: "axil-gpio", kind: "ip" },
        ...mockCatalogV2.items,
      ],
    };
    render(<GeneratorApp catalog={ipFirst} debounceMs={0} />);
    expect(screen.getByRole("option", { name: /^Counter/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await waitFor(() =>
      expect(screen.getByTestId("code").textContent).toContain("module counter"),
    );
  });

  it("disables Run smoke sim for snippets, which have no testbench", async () => {
    render(<GeneratorApp catalog={mockCatalogV2} debounceMs={0} />);
    await waitFor(() =>
      expect(screen.getByTestId("code").textContent).toContain("module counter"),
    );
    expect(screen.getByRole("button", { name: /Run smoke sim/ })).toBeDisabled();
    await userEvent.click(screen.getByRole("option", { name: /Edge Detector/ }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Run smoke sim/ })).toBeEnabled(),
    );
  });
});

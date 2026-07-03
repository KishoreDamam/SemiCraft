import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { DynamicForm, type OptionValues } from "@/components/DynamicForm";
import { counterSchema, counterDefaults } from "@/mocks/schemas/counter";
import { fsmSchema, fsmDefaults } from "@/mocks/schemas/fsm";
import type { JsonSchema } from "@/lib/types";

function Harness({
  schema,
  initial,
  onChangeSpy,
  errors = {},
}: {
  schema: JsonSchema;
  initial: OptionValues;
  onChangeSpy?: (name: string, value: unknown) => void;
  errors?: Record<string, string>;
}) {
  const [values, setValues] = useState<OptionValues>(initial);
  return (
    <DynamicForm
      schema={schema}
      values={values}
      errors={errors}
      onChange={(name, value) => {
        onChangeSpy?.(name, value);
        setValues((p) => ({ ...p, [name]: value }));
      }}
    />
  );
}

describe("DynamicForm — counter schema (segmented, toggle, number)", () => {
  it("prefills defaults across widget types", () => {
    render(<Harness schema={counterSchema} initial={counterDefaults} />);
    // number
    expect(screen.getByLabelText("Width")).toHaveValue(8);
    // toggle (aria-checked reflects default true)
    expect(screen.getByRole("switch", { name: "Enable" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    // segmented (radio for the default option is checked)
    const dir = screen.getByRole("radiogroup", { name: "Direction" });
    expect(within(dir).getByRole("radio", { name: "up" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("segmented control fires onChange with the picked value", async () => {
    const spy = vi.fn();
    render(<Harness schema={counterSchema} initial={counterDefaults} onChangeSpy={spy} />);
    const dir = screen.getByRole("radiogroup", { name: "Direction" });
    await userEvent.click(within(dir).getByRole("radio", { name: "down" }));
    expect(spy).toHaveBeenCalledWith("direction", "down");
  });

  it("toggle flips boolean value", async () => {
    const spy = vi.fn();
    render(<Harness schema={counterSchema} initial={counterDefaults} onChangeSpy={spy} />);
    await userEvent.click(screen.getByRole("switch", { name: "Enable" }));
    expect(spy).toHaveBeenCalledWith("enable", false);
  });

  it("number input reports numeric values", async () => {
    const spy = vi.fn();
    render(<Harness schema={counterSchema} initial={counterDefaults} onChangeSpy={spy} />);
    const width = screen.getByLabelText("Width");
    await userEvent.clear(width);
    await userEvent.type(width, "16");
    expect(spy).toHaveBeenLastCalledWith("width", 16);
    expect(width).toHaveAttribute("min", "1");
    expect(width).toHaveAttribute("max", "1024");
  });

  it("renders inline field errors", () => {
    render(
      <Harness
        schema={counterSchema}
        initial={counterDefaults}
        errors={{ width: "Input should be greater than or equal to 1" }}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/greater than or equal to 1/);
  });

  it("shows a help tooltip carrying the field description", () => {
    render(<Harness schema={counterSchema} initial={counterDefaults} />);
    // The width field description becomes an accessible tooltip trigger.
    expect(screen.getByLabelText(/Help: Counter bit width\./)).toBeInTheDocument();
  });
});

describe("DynamicForm — fsm schema (dropdown-less enums, chips, text)", () => {
  it("renders a chips input for array-of-string with the default items", () => {
    render(<Harness schema={fsmSchema} initial={fsmDefaults} />);
    // default states rendered as removable chips
    expect(screen.getByLabelText("Remove idle")).toBeInTheDocument();
    expect(screen.getByLabelText("Remove run")).toBeInTheDocument();
    expect(screen.getByLabelText("Remove done")).toBeInTheDocument();
  });

  it("chips input adds a unique item on Enter and rejects duplicates", async () => {
    const spy = vi.fn();
    render(<Harness schema={fsmSchema} initial={fsmDefaults} onChangeSpy={spy} />);
    const adder = screen.getByLabelText("Add to States");
    await userEvent.type(adder, "wait{enter}");
    expect(spy).toHaveBeenCalledWith("states", ["idle", "run", "done", "wait"]);

    spy.mockClear();
    // duplicate should not fire onChange
    await userEvent.type(adder, "idle{enter}");
    const stateCalls = spy.mock.calls.filter((c) => c[0] === "states");
    expect(stateCalls).toHaveLength(0);
  });

  it("chips input removes an item", async () => {
    const spy = vi.fn();
    render(<Harness schema={fsmSchema} initial={fsmDefaults} onChangeSpy={spy} />);
    await userEvent.click(screen.getByLabelText("Remove run"));
    expect(spy).toHaveBeenCalledWith("states", ["idle", "done"]);
  });

  it("resolves the encoding enum (via $ref) into a segmented control", async () => {
    const spy = vi.fn();
    render(<Harness schema={fsmSchema} initial={fsmDefaults} onChangeSpy={spy} />);
    const enc = screen.getByRole("radiogroup", { name: "Encoding" });
    await userEvent.click(within(enc).getByRole("radio", { name: "onehot" }));
    expect(spy).toHaveBeenCalledWith("encoding", "onehot");
  });

  it("renders reset_state as a text input", async () => {
    const spy = vi.fn();
    render(<Harness schema={fsmSchema} initial={fsmDefaults} onChangeSpy={spy} />);
    const rs = screen.getByLabelText("Reset State");
    await userEvent.clear(rs);
    await userEvent.type(rs, "run");
    expect(spy).toHaveBeenLastCalledWith("reset_state", "run");
  });
});

describe("DynamicForm — dropdown widget (>4 options)", () => {
  const bigEnum: JsonSchema = {
    type: "object",
    properties: {
      choice: {
        type: "string",
        title: "Choice",
        enum: ["a", "b", "c", "d", "e"],
        default: "a",
      },
    },
  };

  it("renders a select and fires onChange", async () => {
    const spy = vi.fn();
    render(<Harness schema={bigEnum} initial={{ choice: "a" }} onChangeSpy={spy} />);
    const select = screen.getByLabelText("Choice");
    expect(select.tagName).toBe("SELECT");
    await userEvent.selectOptions(select, "c");
    expect(spy).toHaveBeenCalledWith("choice", "c");
  });
});

describe("DynamicForm — constrained chips (comparator outputs)", () => {
  const cmp: JsonSchema = {
    type: "object",
    properties: {
      outputs: {
        type: "array",
        title: "Outputs",
        items: { type: "string", enum: ["eq", "lt", "gt"] },
        default: ["eq"],
      },
    },
  };

  it("toggles a constrained value chip on and off", async () => {
    const spy = vi.fn();
    render(<Harness schema={cmp} initial={{ outputs: ["eq"] }} onChangeSpy={spy} />);
    await userEvent.click(screen.getByRole("button", { name: "lt" }));
    expect(spy).toHaveBeenCalledWith("outputs", ["eq", "lt"]);
  });
});

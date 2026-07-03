"use client";

import { useMemo } from "react";
import type { JsonSchema } from "@/lib/types";
import { describeSchema, type WidgetDescriptor } from "@/lib/schema";
import {
  ChipsInput,
  Dropdown,
  FieldShell,
  NumberInput,
  SegmentedControl,
  Toggle,
} from "@/components/widgets";

/**
 * The schema-driven dynamic form renderer — WP-07 task 2, the product's core
 * IP. Given a JSON Schema and the current option values, it renders the right
 * widget per field with NO per-snippet code:
 *   string/int enum <= 4 -> segmented control, else dropdown
 *   boolean            -> toggle
 *   bounded integer    -> numeric input with min/max
 *   array of string    -> chips input (add/remove, uniqueness)
 * Field descriptions become help tooltips; 422 field errors render inline.
 */

export type OptionValues = Record<string, unknown>;

function widgetInput(
  d: WidgetDescriptor,
  value: unknown,
  onChange: (v: unknown) => void,
  fieldId: string,
  error?: string,
) {
  const invalid = Boolean(error);
  switch (d.kind) {
    case "segmented":
      return (
        <SegmentedControl
          label={d.label}
          value={value as string | number | undefined}
          options={d.options ?? []}
          onChange={onChange}
          invalid={invalid}
        />
      );
    case "dropdown":
      return (
        <Dropdown
          id={fieldId}
          label={d.label}
          value={value as string | number | undefined}
          options={d.options ?? []}
          onChange={onChange}
          invalid={invalid}
        />
      );
    case "toggle":
      return (
        <Toggle
          label={d.label}
          value={Boolean(value)}
          onChange={onChange}
        />
      );
    case "number":
      return (
        <NumberInput
          id={fieldId}
          label={d.label}
          value={value as number | undefined}
          min={d.min}
          max={d.max}
          onChange={onChange}
          invalid={invalid}
        />
      );
    case "chips":
      return (
        <ChipsInput
          label={d.label}
          value={Array.isArray(value) ? (value as string[]) : []}
          onChange={onChange}
          uniqueItems={d.uniqueItems}
          itemEnum={d.itemEnum}
          invalid={invalid}
        />
      );
    default:
      return (
        <input
          id={fieldId}
          aria-label={d.label}
          value={value === undefined ? "" : String(value)}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full rounded border bg-white px-2 py-1 text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 ${
            invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
          }`}
        />
      );
  }
}

export function DynamicForm({
  schema,
  values,
  errors,
  onChange,
}: {
  schema: JsonSchema;
  values: OptionValues;
  errors: Record<string, string>;
  onChange: (name: string, value: unknown) => void;
}) {
  const descriptors = useMemo(() => describeSchema(schema), [schema]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(e) => e.preventDefault()}
      aria-label="Snippet options"
    >
      {descriptors.map((d) => {
        const fieldId = `field-${d.name}`;
        // segmented/toggle/chips are not <input>s; only associate a label
        // htmlFor with widgets that expose a real control id.
        const htmlFor =
          d.kind === "dropdown" || d.kind === "number" || d.kind === "text"
            ? fieldId
            : undefined;
        return (
          <FieldShell
            key={d.name}
            label={d.label}
            htmlFor={htmlFor}
            description={d.description}
            error={errors[d.name]}
          >
            {widgetInput(
              d,
              values[d.name],
              (v) => onChange(d.name, v),
              fieldId,
              errors[d.name],
            )}
          </FieldShell>
        );
      })}
    </form>
  );
}

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
 *   nested sub-model   -> grouped fieldset of the above (e.g. naming style)
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
          value={value === undefined || value === null ? "" : String(value)}
          placeholder={d.nullable ? "(default)" : undefined}
          onChange={(e) =>
            onChange(d.nullable && e.target.value === "" ? null : e.target.value)
          }
          className={`w-full rounded border bg-white px-2 py-1 text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 ${
            invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
          }`}
        />
      );
  }
}

/**
 * One field. A nested sub-model recurses into a fieldset whose children edit
 * their own key and hand the whole merged object back up, so the submitted
 * value keeps the shape the backend's Pydantic model expects.
 */
function Field({
  d,
  value,
  errors,
  onChange,
  idPrefix,
}: {
  d: WidgetDescriptor;
  value: unknown;
  errors: Record<string, string>;
  onChange: (v: unknown) => void;
  idPrefix: string;
}) {
  const fieldId = `${idPrefix}${d.name}`;

  if (d.kind === "nested") {
    const obj =
      value && typeof value === "object" ? (value as Record<string, unknown>) : {};
    return (
      <fieldset
        className="flex flex-col gap-3 rounded border border-zinc-200 p-3 dark:border-zinc-800"
        data-field
      >
        <legend className="px-1 text-xs font-medium text-zinc-700 dark:text-zinc-300">
          {d.label}
        </legend>
        {(d.fields ?? []).map((sub) => (
          <Field
            key={sub.name}
            d={sub}
            value={obj[sub.name]}
            errors={errors}
            onChange={(v) => onChange({ ...obj, [sub.name]: v })}
            idPrefix={`${fieldId}-`}
          />
        ))}
      </fieldset>
    );
  }

  // segmented/toggle/chips are not <input>s; only associate a label
  // htmlFor with widgets that expose a real control id.
  const htmlFor =
    d.kind === "dropdown" || d.kind === "number" || d.kind === "text"
      ? fieldId
      : undefined;
  return (
    <FieldShell
      label={d.label}
      htmlFor={htmlFor}
      description={d.description}
      error={errors[d.name]}
    >
      {widgetInput(d, value, onChange, fieldId, errors[d.name])}
    </FieldShell>
  );
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
      {descriptors.map((d) => (
        <Field
          key={d.name}
          d={d}
          value={values[d.name]}
          errors={errors}
          onChange={(v) => onChange(d.name, v)}
          idPrefix="field-"
        />
      ))}
    </form>
  );
}

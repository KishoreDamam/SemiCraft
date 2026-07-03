"use client";

import { useId, useState } from "react";
import type { EnumOption } from "@/lib/schema";

/**
 * Low-level, controlled form widgets used by the dynamic form renderer.
 * Each is presentation-only; validation state (error text) is passed in.
 * No per-snippet logic lives here.
 */

export function HelpTooltip({ text }: { text: string }) {
  return (
    <span className="group relative ml-1 inline-flex align-middle">
      <span
        tabIndex={0}
        role="img"
        aria-label={`Help: ${text}`}
        className="flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-zinc-400 text-[10px] leading-none text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-600 dark:text-zinc-400"
      >
        ?
      </span>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-6 z-20 w-56 -translate-x-1/2 rounded border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-700 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
      >
        {text}
      </span>
    </span>
  );
}

export function FieldShell({
  label,
  htmlFor,
  description,
  error,
  children,
}: {
  label: string;
  htmlFor?: string;
  description?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1" data-field>
      <label
        htmlFor={htmlFor}
        className="flex items-center text-xs font-medium text-zinc-700 dark:text-zinc-300"
      >
        {label}
        {description ? <HelpTooltip text={description} /> : null}
      </label>
      {children}
      {error ? (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function SegmentedControl({
  value,
  options,
  onChange,
  label,
  invalid,
}: {
  value: string | number | undefined;
  options: EnumOption[];
  onChange: (v: string | number) => void;
  label: string;
  invalid?: boolean;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={`inline-flex overflow-hidden rounded border ${
        invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
      }`}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={String(opt.value)}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={`px-3 py-1 text-xs transition-colors ${
              active
                ? "bg-blue-600 text-white"
                : "bg-white text-zinc-700 hover:bg-zinc-100 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
            } ${opt !== options[options.length - 1] ? "border-r border-zinc-300 dark:border-zinc-700" : ""}`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export function Dropdown({
  id,
  value,
  options,
  onChange,
  label,
  invalid,
}: {
  id?: string;
  value: string | number | undefined;
  options: EnumOption[];
  onChange: (v: string | number) => void;
  label: string;
  invalid?: boolean;
}) {
  // Enum values may be numbers; keep a string index to map back.
  return (
    <select
      id={id}
      aria-label={label}
      value={value === undefined ? "" : String(value)}
      onChange={(e) => {
        const chosen = options.find((o) => String(o.value) === e.target.value);
        if (chosen) onChange(chosen.value);
      }}
      className={`w-full rounded border bg-white px-2 py-1 text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 ${
        invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
      }`}
    >
      {options.map((opt) => (
        <option key={String(opt.value)} value={String(opt.value)}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function Toggle({
  value,
  onChange,
  label,
}: {
  value: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={value}
      aria-label={label}
      onClick={() => onChange(!value)}
      className={`relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full transition-colors ${
        value ? "bg-blue-600" : "bg-zinc-300 dark:bg-zinc-700"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          value ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

export function NumberInput({
  id,
  value,
  onChange,
  min,
  max,
  label,
  invalid,
}: {
  id?: string;
  value: number | undefined;
  onChange: (v: number | undefined) => void;
  min?: number;
  max?: number;
  label: string;
  invalid?: boolean;
}) {
  return (
    <input
      id={id}
      type="number"
      aria-label={label}
      value={value === undefined || Number.isNaN(value) ? "" : value}
      min={min}
      max={max}
      onChange={(e) => {
        const raw = e.target.value;
        if (raw === "") {
          onChange(undefined);
          return;
        }
        const n = Number(raw);
        onChange(Number.isNaN(n) ? undefined : n);
      }}
      className={`w-full rounded border bg-white px-2 py-1 text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 ${
        invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
      }`}
    />
  );
}

/**
 * Tag / chips input for array-of-string options (FSM states/outputs,
 * comparator outputs). Add on Enter/comma, remove via the chip's x button.
 * Enforces uniqueness and (when itemEnum is present) a constrained value set.
 */
export function ChipsInput({
  value,
  onChange,
  label,
  uniqueItems = true,
  itemEnum,
  invalid,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  label: string;
  uniqueItems?: boolean;
  itemEnum?: EnumOption[];
  invalid?: boolean;
}) {
  const [draft, setDraft] = useState("");
  const inputId = useId();

  const commit = (raw: string) => {
    const item = raw.trim();
    if (!item) return;
    if (uniqueItems && value.includes(item)) {
      setDraft("");
      return;
    }
    onChange([...value, item]);
    setDraft("");
  };

  const remove = (idx: number) => {
    onChange(value.filter((_, i) => i !== idx));
  };

  // Constrained set (e.g. comparator outputs): render selectable chips.
  if (itemEnum) {
    return (
      <div
        aria-label={label}
        role="group"
        className={`flex flex-wrap gap-1 rounded border p-1 ${
          invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
        }`}
      >
        {itemEnum.map((opt) => {
          const selected = value.includes(String(opt.value));
          return (
            <button
              key={String(opt.value)}
              type="button"
              aria-pressed={selected}
              onClick={() =>
                selected
                  ? onChange(value.filter((v) => v !== String(opt.value)))
                  : onChange([...value, String(opt.value)])
              }
              className={`rounded px-2 py-0.5 text-xs transition-colors ${
                selected
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div
      className={`flex flex-wrap items-center gap-1 rounded border p-1 ${
        invalid ? "border-red-500" : "border-zinc-300 dark:border-zinc-700"
      }`}
    >
      {value.map((item, idx) => (
        <span
          key={`${item}-${idx}`}
          className="inline-flex items-center gap-1 rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800 dark:bg-blue-900/50 dark:text-blue-200"
        >
          {item}
          <button
            type="button"
            aria-label={`Remove ${item}`}
            onClick={() => remove(idx)}
            className="text-blue-500 hover:text-blue-700 dark:text-blue-300"
          >
            ×
          </button>
        </span>
      ))}
      <input
        id={inputId}
        aria-label={`Add to ${label}`}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            commit(draft);
          } else if (e.key === "Backspace" && draft === "" && value.length > 0) {
            remove(value.length - 1);
          }
        }}
        onBlur={() => commit(draft)}
        placeholder="add…"
        className="min-w-[4rem] flex-1 bg-transparent px-1 py-0.5 text-xs text-zinc-800 outline-none dark:text-zinc-200"
      />
    </div>
  );
}

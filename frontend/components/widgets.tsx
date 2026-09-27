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
        className="flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-rule-strong font-mono text-[9px] leading-none text-ink-3 hover:border-ink-2 hover:text-ink"
      >
        ?
      </span>
      <span
        role="tooltip"
        className="pointer-events-none invisible absolute left-0 top-5 z-20 w-64 rounded-sm bg-ink px-2.5 py-2 text-xs font-normal normal-case leading-relaxed tracking-normal text-paper group-hover:visible group-focus-within:visible"
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
    <div className="flex flex-col gap-1.5" data-field>
      <label
        htmlFor={htmlFor}
        className="flex items-center gap-1.5 text-[13px] font-medium text-ink-2"
      >
        {label}
        {description ? <HelpTooltip text={description} /> : null}
      </label>
      {children}
      {error ? (
        <p role="alert" className="text-xs text-err">
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
      className={`grid auto-cols-fr grid-flow-col overflow-hidden rounded-sm border bg-sheet ${
        invalid ? "border-err" : "border-rule-strong"
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
            className={`h-8 truncate px-2.5 text-[13px] ${
              active
                ? "bg-ink font-medium text-paper"
                : "text-ink-2 hover:bg-well hover:text-ink"
            } ${opt !== options[options.length - 1] ? "border-r border-rule-strong" : ""}`}
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
      className={`h-8 w-full rounded-sm border bg-sheet px-2 text-[13px] text-ink ${
        invalid ? "border-err" : "border-rule-strong hover:border-ink-3"
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
  // The state is written beside the switch too: a filled block alone does not
  // say which way is on.
  return (
    <span className="inline-flex items-center gap-2.5">
      <button
        type="button"
        role="switch"
        aria-checked={value}
        aria-label={label}
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-sm border ${
          value ? "border-ink bg-ink" : "border-rule-strong bg-well"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 rounded-[2px] transition-transform duration-100 ${
            value ? "translate-x-[22px] bg-paper" : "translate-x-[3px] bg-ink-3"
          }`}
        />
        <span className="sr-only">{value ? "on" : "off"}</span>
      </button>
      <span aria-hidden className="font-mono text-xs text-ink-3">
        {value ? "On" : "Off"}
      </span>
    </span>
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
      className={`h-8 w-full rounded-sm border bg-sheet px-2 font-mono text-[13px] text-ink ${
        invalid ? "border-err" : "border-rule-strong hover:border-ink-3"
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
        className={`flex flex-wrap gap-1.5 ${invalid ? "rounded-sm outline outline-1 outline-err" : ""}`}
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
              className={`h-7 rounded-sm border px-2 font-mono text-xs ${
                selected
                  ? "border-ink bg-ink text-paper"
                  : "border-rule-strong bg-sheet text-ink-2 hover:border-ink-3 hover:text-ink"
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
      className={`flex min-h-8 flex-wrap items-center gap-1 rounded-sm border bg-sheet p-1 focus-within:border-ink-3 ${
        invalid ? "border-err" : "border-rule-strong"
      }`}
    >
      {value.map((item, idx) => (
        <span
          key={`${item}-${idx}`}
          className="inline-flex h-6 items-center gap-1 rounded-sm bg-well pl-2 pr-1 font-mono text-xs text-ink"
        >
          {item}
          <button
            type="button"
            aria-label={`Remove ${item}`}
            onClick={() => remove(idx)}
            className="flex h-4 w-4 items-center justify-center rounded-sm text-ink-3 hover:bg-ink hover:text-paper"
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
        className="min-w-[4rem] flex-1 bg-transparent px-1 font-mono text-xs text-ink outline-none placeholder:text-ink-3"
      />
    </div>
  );
}

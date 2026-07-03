import type { JsonSchema } from "@/lib/types";

/**
 * Hand-authored JSON Schema for the `fsm` hero snippet (WP-05i), matching
 * Pydantic v2 output for the options table in IMPLEMENTATION_PLAN.md §5.
 *
 * This schema deliberately uses the $defs + allOf/$ref INDIRECTION that
 * Pydantic v2 emits for named Enum types (encoding, machine). The renderer's
 * schema resolver (lib/schema.ts) must follow these refs to recover the enum
 * options and the field description (§8 risk: JSON Schema fidelity). It also
 * exercises the array-of-string widget for `states` and `outputs`.
 */
export const fsmSchema: JsonSchema = {
  type: "object",
  title: "FsmOptions",
  $defs: {
    Encoding: {
      type: "string",
      title: "Encoding",
      enum: ["binary", "onehot", "gray"],
    },
    Machine: {
      type: "string",
      title: "Machine",
      enum: ["moore", "mealy"],
    },
    Language: {
      type: "string",
      title: "Language",
      enum: ["sv", "verilog"],
    },
  },
  properties: {
    // CommonOptions subset relevant to FSM (clocked snippet).
    language: {
      allOf: [{ $ref: "#/$defs/Language" }],
      title: "Language",
      description: "Target HDL. SystemVerilog is the default.",
      default: "sv",
    },
    reset_style: {
      type: "string",
      title: "Reset Style",
      description: "Synchronous or asynchronous reset.",
      enum: ["sync", "async"],
      default: "sync",
    },
    reset_polarity: {
      type: "string",
      title: "Reset Polarity",
      description: "Active-high or active-low reset.",
      enum: ["active_high", "active_low"],
      default: "active_low",
    },
    include_wrapper: {
      type: "boolean",
      title: "Include Wrapper",
      description: "Emit a full module wrapper. Disable for fragment mode.",
      default: true,
    },
    // FSM-specific.
    states: {
      type: "array",
      title: "States",
      description:
        "State names (2-16). Each must be a unique, valid identifier.",
      items: { type: "string" },
      minItems: 2,
      maxItems: 16,
      uniqueItems: true,
      default: ["idle", "run", "done"],
    },
    encoding: {
      // Pydantic-style: $ref via allOf, with the description on the property.
      allOf: [{ $ref: "#/$defs/Encoding" }],
      title: "Encoding",
      description: "State encoding scheme.",
      default: "binary",
    },
    machine: {
      allOf: [{ $ref: "#/$defs/Machine" }],
      title: "Machine",
      description: "Moore (outputs depend on state) or Mealy (state + inputs).",
      default: "moore",
    },
    reset_state: {
      type: "string",
      title: "Reset State",
      description: "State entered on reset. Must be one of the declared states.",
      default: "idle",
    },
    outputs: {
      type: "array",
      title: "Outputs",
      description: "Output signal names (0-8). Each a unique identifier.",
      items: { type: "string" },
      minItems: 0,
      maxItems: 8,
      uniqueItems: true,
      default: ["busy"],
    },
  },
  required: [],
};

export const fsmDefaults: Record<string, unknown> = {
  language: "sv",
  reset_style: "sync",
  reset_polarity: "active_low",
  include_wrapper: true,
  states: ["idle", "run", "done"],
  encoding: "binary",
  machine: "moore",
  reset_state: "idle",
  outputs: ["busy"],
};

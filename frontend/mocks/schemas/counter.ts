import type { JsonSchema } from "@/lib/types";

/**
 * Hand-authored JSON Schema for the `counter` snippet, matching what Pydantic
 * v2 `model_json_schema()` would emit for the WP-03 counter options model
 * (IMPLEMENTATION_PLAN.md §5 WP-03 task 3) plus the CommonOptions mixin (§3).
 *
 * Enums here are emitted INLINE (`enum` on the property) to exercise the
 * inline-enum path of the renderer. The fsm schema uses the $defs/$ref path.
 * Both are valid Pydantic v2 output shapes.
 */
export const counterSchema: JsonSchema = {
  type: "object",
  title: "CounterOptions",
  properties: {
    // ---- CommonOptions ----
    language: {
      type: "string",
      title: "Language",
      description: "Target HDL. SystemVerilog is the default.",
      enum: ["sv", "verilog"],
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
      description: "Active-high or active-low reset (active-low uses an _n suffix).",
      enum: ["active_high", "active_low"],
      default: "active_low",
    },
    comment_verbosity: {
      type: "string",
      title: "Comment Verbosity",
      description: "How many explanatory comments to emit in the generated RTL.",
      enum: ["none", "normal", "verbose"],
      default: "normal",
    },
    include_wrapper: {
      type: "boolean",
      title: "Include Wrapper",
      description: "Emit a full module wrapper. Disable for paste-in fragment mode.",
      default: true,
    },
    // ---- Counter-specific ----
    width: {
      type: "integer",
      title: "Width",
      description: "Counter bit width.",
      minimum: 1,
      maximum: 1024,
      default: 8,
    },
    direction: {
      type: "string",
      title: "Direction",
      description: "Count up, down, or up/down (up/down adds an up_dn input).",
      enum: ["up", "down", "updown"],
      default: "up",
    },
    enable: {
      type: "boolean",
      title: "Enable",
      description: "Add a synchronous enable input.",
      default: true,
    },
    wrap: {
      type: "string",
      title: "Wrap",
      description: "Overflow wraps around, or saturates at the limit.",
      enum: ["overflow", "saturate"],
      default: "overflow",
    },
    reset_value: {
      type: "integer",
      title: "Reset Value",
      description: "Value loaded on reset. Must be less than 2^width.",
      minimum: 0,
      default: 0,
    },
  },
  required: [],
};

export const counterDefaults: Record<string, unknown> = {
  language: "sv",
  reset_style: "sync",
  reset_polarity: "active_low",
  comment_verbosity: "normal",
  include_wrapper: true,
  width: 8,
  direction: "up",
  enable: true,
  wrap: "overflow",
  reset_value: 0,
};

import type { CatalogResponse, JsonSchema, SnippetCatalogEntry } from "@/lib/types";
import { counterSchema, counterDefaults } from "@/mocks/schemas/counter";
import { fsmSchema, fsmDefaults } from "@/mocks/schemas/fsm";

// ---- Reusable CommonOptions fragments (clocked snippets) ----

const commonClockedProps: Record<string, JsonSchema> = {
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
    description: "Active-high or active-low reset.",
    enum: ["active_high", "active_low"],
    default: "active_low",
  },
  comment_verbosity: {
    type: "string",
    title: "Comment Verbosity",
    description: "How many explanatory comments to emit.",
    enum: ["none", "normal", "verbose"],
    default: "normal",
  },
  include_wrapper: {
    type: "boolean",
    title: "Include Wrapper",
    description: "Emit a full module wrapper (off = fragment mode).",
    default: true,
  },
};

const commonClockedDefaults = {
  language: "sv",
  reset_style: "sync",
  reset_polarity: "active_low",
  comment_verbosity: "normal",
  include_wrapper: true,
};

// Combinational snippets omit reset/clock fields (WP-05 note).
const commonCombProps: Record<string, JsonSchema> = {
  language: commonClockedProps.language,
  comment_verbosity: commonClockedProps.comment_verbosity,
  include_wrapper: commonClockedProps.include_wrapper,
};

const commonCombDefaults = {
  language: "sv",
  comment_verbosity: "normal",
  include_wrapper: true,
};

function objectSchema(
  title: string,
  props: Record<string, JsonSchema>,
): JsonSchema {
  return { type: "object", title, properties: props, required: [] };
}

// ---- register (WP-05a) ----
const registerSchema = objectSchema("RegisterOptions", {
  ...commonClockedProps,
  width: {
    type: "integer",
    title: "Width",
    description: "Register bit width.",
    minimum: 1,
    maximum: 1024,
    default: 8,
  },
  enable: {
    type: "boolean",
    title: "Enable",
    description: "Add a synchronous enable input.",
    default: true,
  },
  reset_value: {
    type: "integer",
    title: "Reset Value",
    description: "Value loaded on reset.",
    minimum: 0,
    default: 0,
  },
  clear_input: {
    type: "boolean",
    title: "Clear Input",
    description: "Add a synchronous clear port (clear beats enable).",
    default: false,
  },
});
const registerDefaults = {
  ...commonClockedDefaults,
  width: 8,
  enable: true,
  reset_value: 0,
  clear_input: false,
};

// ---- shift-register (WP-05b) ----
const shiftRegisterSchema = objectSchema("ShiftRegisterOptions", {
  ...commonClockedProps,
  depth: {
    type: "integer",
    title: "Depth",
    description: "Number of stages.",
    minimum: 2,
    maximum: 256,
    default: 8,
  },
  direction: {
    type: "string",
    title: "Direction",
    description: "Shift direction.",
    enum: ["left", "right"],
    default: "right",
  },
  parallel_load: {
    type: "boolean",
    title: "Parallel Load",
    description: "Add load and parallel data ports.",
    default: false,
  },
  serial_out_only: {
    type: "boolean",
    title: "Serial Out Only",
    description: "Expose only the serial output.",
    default: false,
  },
});
const shiftRegisterDefaults = {
  ...commonClockedDefaults,
  depth: 8,
  direction: "right",
  parallel_load: false,
  serial_out_only: false,
};

// ---- mux (WP-05c) ----
const muxSchema = objectSchema("MuxOptions", {
  ...commonCombProps,
  num_inputs: {
    type: "integer",
    title: "Num Inputs",
    description: "Number of data inputs (in0..inN-1).",
    minimum: 2,
    maximum: 16,
    default: 4,
  },
  width: {
    type: "integer",
    title: "Width",
    description: "Data width per input.",
    minimum: 1,
    maximum: 512,
    default: 8,
  },
  impl: {
    type: "string",
    title: "Impl",
    description: "Implementation style.",
    enum: ["case", "ternary"],
    default: "case",
  },
});
const muxDefaults = {
  ...commonCombDefaults,
  num_inputs: 4,
  width: 8,
  impl: "case",
};

// ---- demux (WP-05d) ----
const demuxSchema = objectSchema("DemuxOptions", {
  ...commonCombProps,
  num_outputs: {
    type: "integer",
    title: "Num Outputs",
    description: "Number of data outputs.",
    minimum: 2,
    maximum: 16,
    default: 4,
  },
  width: {
    type: "integer",
    title: "Width",
    description: "Data width.",
    minimum: 1,
    maximum: 512,
    default: 8,
  },
  default_value: {
    type: "string",
    title: "Default Value",
    description: "Value on un-selected outputs (MVP is combinational: zeros only).",
    enum: ["zeros"],
    default: "zeros",
  },
});
const demuxDefaults = {
  ...commonCombDefaults,
  num_outputs: 4,
  width: 8,
  default_value: "zeros",
};

// ---- encoder (WP-05e) ----
const encoderSchema = objectSchema("EncoderOptions", {
  ...commonCombProps,
  kind: {
    type: "string",
    title: "Kind",
    description: "Priority or one-hot encoder.",
    enum: ["priority", "onehot"],
    default: "priority",
  },
  num_inputs: {
    type: "integer",
    title: "Num Inputs",
    description: "Number of inputs.",
    enum: [4, 8, 16],
    default: 8,
  },
  valid_output: {
    type: "boolean",
    title: "Valid Output",
    description: "Add a valid output signal.",
    default: true,
  },
});
const encoderDefaults = {
  ...commonCombDefaults,
  kind: "priority",
  num_inputs: 8,
  valid_output: true,
};

// ---- decoder (WP-05f) ----
const decoderSchema = objectSchema("DecoderOptions", {
  ...commonCombProps,
  num_outputs: {
    type: "integer",
    title: "Num Outputs",
    description: "Number of decoded outputs.",
    enum: [2, 4, 8, 16],
    default: 8,
  },
  enable: {
    type: "boolean",
    title: "Enable",
    description: "Add an enable input.",
    default: true,
  },
  output_polarity: {
    type: "string",
    title: "Output Polarity",
    description: "Active-high or active-low outputs.",
    enum: ["active_high", "active_low"],
    default: "active_high",
  },
});
const decoderDefaults = {
  ...commonCombDefaults,
  num_outputs: 8,
  enable: true,
  output_polarity: "active_high",
};

// ---- comparator (WP-05g) ----
const comparatorSchema = objectSchema("ComparatorOptions", {
  ...commonCombProps,
  width: {
    type: "integer",
    title: "Width",
    description: "Operand width.",
    minimum: 1,
    maximum: 512,
    default: 8,
  },
  signed: {
    type: "boolean",
    title: "Signed",
    description: "Treat operands as signed.",
    default: false,
  },
  outputs: {
    type: "array",
    title: "Outputs",
    description: "Comparison outputs to emit (at least one).",
    items: { type: "string", enum: ["eq", "ne", "lt", "le", "gt", "ge"] },
    minItems: 1,
    maxItems: 6,
    uniqueItems: true,
    default: ["eq", "lt", "gt"],
  },
});
const comparatorDefaults = {
  ...commonCombDefaults,
  width: 8,
  signed: false,
  outputs: ["eq", "lt", "gt"],
};

// ---- cdc-synchronizer (WP-05h) ----
const cdcSchema = objectSchema("CdcSynchronizerOptions", {
  ...commonClockedProps,
  stages: {
    type: "integer",
    title: "Stages",
    description: "Number of synchronizer flip-flops.",
    minimum: 2,
    maximum: 4,
    default: 2,
  },
  width: {
    type: "integer",
    title: "Width",
    description: "Signal width. >1 only safe for gray-coded/quasi-static signals.",
    minimum: 1,
    maximum: 8,
    default: 1,
  },
  use_reset: {
    type: "boolean",
    title: "Use Reset",
    description: "Add a reset to the synchronizer chain.",
    default: false,
  },
});
const cdcDefaults = {
  ...commonClockedDefaults,
  stages: 2,
  width: 1,
  use_reset: false,
};

const entries: SnippetCatalogEntry[] = [
  {
    id: "counter",
    name: "Counter",
    description: "Parameterized up/down counter with enable and wrap/saturate.",
    json_schema: counterSchema,
    defaults: counterDefaults,
  },
  {
    id: "register",
    name: "Register",
    description: "Clocked register with optional enable and synchronous clear.",
    json_schema: registerSchema,
    defaults: registerDefaults,
  },
  {
    id: "shift-register",
    name: "Shift Register",
    description: "Serial/parallel shift register with configurable depth and direction.",
    json_schema: shiftRegisterSchema,
    defaults: shiftRegisterDefaults,
  },
  {
    id: "mux",
    name: "Mux",
    description: "N-to-1 multiplexer (case or ternary implementation).",
    json_schema: muxSchema,
    defaults: muxDefaults,
  },
  {
    id: "demux",
    name: "Demux",
    description: "1-to-N demultiplexer with zeroed idle outputs.",
    json_schema: demuxSchema,
    defaults: demuxDefaults,
  },
  {
    id: "encoder",
    name: "Encoder",
    description: "Priority or one-hot encoder with optional valid output.",
    json_schema: encoderSchema,
    defaults: encoderDefaults,
  },
  {
    id: "decoder",
    name: "Decoder",
    description: "Binary-to-one-hot decoder with enable and output polarity.",
    json_schema: decoderSchema,
    defaults: decoderDefaults,
  },
  {
    id: "comparator",
    name: "Comparator",
    description: "Magnitude/equality comparator with selectable outputs.",
    json_schema: comparatorSchema,
    defaults: comparatorDefaults,
  },
  {
    id: "cdc-synchronizer",
    name: "CDC Synchronizer",
    description: "Multi-stage two-flip-flop clock-domain-crossing synchronizer.",
    json_schema: cdcSchema,
    defaults: cdcDefaults,
  },
  {
    id: "fsm",
    name: "FSM Template",
    description: "Moore/Mealy finite state machine skeleton with encoding choice.",
    json_schema: fsmSchema,
    defaults: fsmDefaults,
  },
];

export const mockCatalog: CatalogResponse = { snippets: entries };

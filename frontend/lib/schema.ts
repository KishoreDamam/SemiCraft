import type { JsonSchema, JsonSchemaType } from "@/lib/types";

/**
 * Schema interpretation layer. The dynamic form renderer (the product's core
 * IP) reads WidgetDescriptors, never raw JSON Schema. All the "understand what
 * Pydantic emitted" logic lives here so the renderer stays declarative.
 */

export type WidgetKind =
  | "segmented" // string/int enum, <= 4 options
  | "dropdown" // string/int enum, > 4 options
  | "toggle" // boolean
  | "number" // bounded integer/number
  | "chips" // array of string
  | "text" // string fallback
  | "nested"; // nested object (e.g. Pydantic sub-model like NamingOptions)

export interface EnumOption {
  value: string | number;
  label: string;
}

export interface WidgetDescriptor {
  name: string; // property key
  label: string; // human title
  description?: string;
  kind: WidgetKind;
  default?: unknown;
  // enum widgets
  options?: EnumOption[];
  // number widgets (inclusive bounds after normalising exclusive variants)
  min?: number;
  max?: number;
  integer?: boolean;
  // chips widgets
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  itemEnum?: EnumOption[]; // constrained set for chip values (e.g. comparator)
}

const SEGMENTED_MAX_OPTIONS = 4;

/** Follow $ref (only local #/$defs/... refs, as Pydantic emits). */
function resolveRef(ref: string, root: JsonSchema): JsonSchema | undefined {
  const m = /^#\/\$defs\/(.+)$/.exec(ref);
  if (!m || !root.$defs) return undefined;
  return root.$defs[m[1]];
}

/**
 * Merge a property schema with anything it points at via $ref / allOf so that
 * enum/type/bounds are visible regardless of whether Pydantic inlined them or
 * indirected through $defs. The property's own keywords win (description,
 * default, title) since Pydantic puts those on the property, not the $def.
 */
export function flattenSchema(schema: JsonSchema, root: JsonSchema): JsonSchema {
  let base: JsonSchema = {};

  if (schema.$ref) {
    const target = resolveRef(schema.$ref, root);
    if (target) base = { ...base, ...flattenSchema(target, root) };
  }
  if (schema.allOf) {
    for (const sub of schema.allOf) {
      base = { ...base, ...flattenSchema(sub, root) };
    }
  }
  // anyOf is how Pydantic encodes Optional[...] / unions; take the first
  // non-null branch that carries type/enum info (sufficient for MVP options).
  if (schema.anyOf) {
    const branch = schema.anyOf.find((s) => s.type !== "null");
    if (branch) base = { ...base, ...flattenSchema(branch, root) };
  }

  // The property's own keywords override the referenced definition's.
  const merged: JsonSchema = { ...base, ...schema };
  // Don't let indirection keywords linger.
  delete merged.$ref;
  delete merged.allOf;
  delete merged.anyOf;
  return merged;
}

function primaryType(s: JsonSchema): JsonSchemaType | undefined {
  if (Array.isArray(s.type)) return s.type.find((t) => t !== "null");
  return s.type;
}

function labelFor(value: unknown): string {
  return String(value);
}

function toEnumOptions(values: unknown[]): EnumOption[] {
  return values.map((v) => ({
    value: v as string | number,
    label: labelFor(v),
  }));
}

/** Build a WidgetDescriptor for one property. */
export function describeField(
  name: string,
  rawSchema: JsonSchema,
  root: JsonSchema,
): WidgetDescriptor {
  const s = flattenSchema(rawSchema, root);
  const label = s.title ?? humanize(name);
  const common = {
    name,
    label,
    description: s.description,
    default: s.default,
  };

  const type = primaryType(s);

  // Enum (string or integer) -> segmented or dropdown.
  if (s.enum && s.enum.length > 0) {
    const options = toEnumOptions(s.enum);
    return {
      ...common,
      kind: options.length <= SEGMENTED_MAX_OPTIONS ? "segmented" : "dropdown",
      options,
    };
  }

  if (type === "boolean") {
    return { ...common, kind: "toggle" };
  }

  if (type === "integer" || type === "number") {
    const { min, max } = normaliseBounds(s);
    return {
      ...common,
      kind: "number",
      min,
      max,
      integer: type === "integer",
    };
  }

  // Nested object (Pydantic sub-model reached via $ref, e.g. NamingOptions).
  // The flat MVP form has no widget for these; mark them so the renderer can
  // skip them. Their value still round-trips via the snippet defaults.
  if (type === "object" || s.properties) {
    return { ...common, kind: "nested" };
  }

  if (type === "array") {
    const item = s.items ? flattenSchema(s.items, root) : {};
    const itemEnum =
      item.enum && item.enum.length > 0 ? toEnumOptions(item.enum) : undefined;
    return {
      ...common,
      kind: "chips",
      minItems: s.minItems,
      maxItems: s.maxItems,
      uniqueItems: s.uniqueItems ?? true,
      itemEnum,
    };
  }

  // string / fallback
  return { ...common, kind: "text" };
}

/** Normalise Pydantic's inclusive/exclusive numeric bounds to inclusive. */
function normaliseBounds(s: JsonSchema): { min?: number; max?: number } {
  let min = s.minimum;
  let max = s.maximum;
  if (s.exclusiveMinimum !== undefined) {
    min = Math.floor(s.exclusiveMinimum) + 1;
  }
  if (s.exclusiveMaximum !== undefined) {
    max = Math.ceil(s.exclusiveMaximum) - 1;
  }
  return { min, max };
}

/** Ordered list of widget descriptors for an object schema's properties. */
export function describeSchema(root: JsonSchema): WidgetDescriptor[] {
  if (!root.properties) return [];
  return Object.entries(root.properties)
    .map(([name, sub]) => describeField(name, sub, root))
    // Nested-object fields have no flat widget; they submit at their default.
    .filter((d) => d.kind !== "nested");
}

function humanize(name: string): string {
  return name
    .split("_")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

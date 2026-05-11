// Rendering helpers for `bank_rules.current_value` — every rule wraps its
// value in `{"value": ...}`. The inner shape ranges from scalars (number,
// boolean, string) to flat arrays of strings (chargeoff_dpd_codes) to arrays
// of band objects (score_bands) and even nested maps (tier_interest_rates).
// The legacy `String(value)` rendering produced "[object Object]" for the
// last few — these helpers fix that.

export function unwrapRuleValue(currentValue: Record<string, unknown> | null | undefined): unknown {
  if (!currentValue) return undefined
  // Rules consistently wrap their payload in {"value": ...}; fall through to
  // the whole object if a future seed forgets the wrapper.
  return 'value' in currentValue ? (currentValue as { value: unknown }).value : currentValue
}

/** Compact summary for table cells. Truncates long collections. */
export function summarizeRuleValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number' || typeof value === 'string') return String(value)

  if (Array.isArray(value)) {
    if (value.length === 0) return '[]'
    // Flat array of primitives → comma-joined
    if (value.every((v) => typeof v !== 'object' || v === null)) {
      const joined = value.map((v) => String(v)).join(', ')
      return joined.length > 80 ? joined.slice(0, 77) + '…' : joined
    }
    // Array of objects (bands) → "4 bands: PRIME, NEAR_PRIME, …"
    const labels = (value as Array<Record<string, unknown>>)
      .map((row) => row.label ?? row.tier ?? row.name)
      .filter((l) => typeof l === 'string') as string[]
    if (labels.length > 0) return `${value.length} items · ${labels.join(', ')}`
    return `${value.length} items`
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (entries.length === 0) return '{}'
    const kvs = entries.slice(0, 4).map(([k, v]) => `${k}: ${typeof v === 'object' ? '{…}' : v}`).join(', ')
    return entries.length > 4 ? `${kvs}, …` : kvs
  }

  return String(value)
}

/** Pretty-printed JSON for modals / detail views. */
export function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function isComplexValue(value: unknown): boolean {
  return typeof value === 'object' && value !== null
}

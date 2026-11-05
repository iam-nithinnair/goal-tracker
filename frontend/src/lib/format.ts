/** "-" when there is nothing to score (the API sends null), otherwise a whole percent. */
export const pct = (v: number | null | undefined) => (v == null ? '-' : `${Math.round(v * 100)}%`)

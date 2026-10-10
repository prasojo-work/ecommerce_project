"use client";

import { SORT_OPTIONS, type Sort } from "@/lib/catalog-query";

/**
 * The sort control `UX.md` section 6 names.
 *
 * A client component for one reason: applying a sort as soon as it changes is what makes a select
 * feel like a select. It submits the form it sits in rather than pushing a URL, so the navigation
 * is the very same one the Apply button makes — the URL stays the single source of state and the
 * back button keeps working. Without JavaScript nothing breaks; the select simply waits for Apply,
 * which is why it lives inside a form that has one.
 *
 * `value` rather than `defaultValue`: the server re-renders this on every navigation, and a
 * `defaultValue` would leave the control showing a stale choice after the back button.
 */
export function SortSelect({ value }: { value: Sort }) {
  return (
    <select
      id="catalog-sort"
      name="sort"
      value={value}
      onChange={(event) => event.currentTarget.form?.requestSubmit()}
      className="min-h-11 w-full rounded-lg border border-border bg-surface px-3 text-base text-ink"
    >
      {SORT_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

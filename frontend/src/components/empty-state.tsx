import type { ReactNode } from "react";

/**
 * The no-products state.
 *
 * Two different situations reach it, and they are not the same thing:
 *
 * - An empty catalog, where `UX.md` section 5 fixes the copy as "No products yet".
 * - A search or filter that matched nothing, which `US-1.3` asks to be reported "with a recovery
 *   suggestion" — so this variant takes a `description` and an `action` that lead somewhere.
 *
 * The description is optional because the empty-catalog case has nothing useful to suggest.
 */
export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mt-8 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
      <h2 className="text-xl">{title}</h2>
      {description ? <p className="mx-auto mt-3 max-w-measure text-muted">{description}</p> : null}
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </div>
  );
}

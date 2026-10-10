/**
 * The no-products state, named in `UX.md` section 5 as "No products yet".
 *
 * `US-1.3` asks the *no search results* variant for a recovery suggestion. That needs filters to
 * exist before the suggestion can point anywhere, so it arrives with `M1.7` rather than offering
 * a way out that does not exist yet.
 */
export function EmptyState({ title }: { title: string }) {
  return (
    <div className="mt-8 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
      <h2 className="text-xl">{title}</h2>
    </div>
  );
}

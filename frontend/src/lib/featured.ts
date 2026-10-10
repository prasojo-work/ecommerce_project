import type { ProductCard } from "@/api/client";

/**
 * How many pieces the home page shows. Four fills one row of `GRID_COLUMNS` at its widest.
 *
 * Nothing specifies the number: `US-1.5` asks only for "a featured grid", and `UX.md` names the
 * section without a count.
 */
export const FEATURED_COUNT = 4;

/**
 * Pick the featured pieces: the most expensive product of each part of the collection.
 *
 * `US-1.5` asks for "featured products", but nothing in the repository defines what *featured*
 * means — there is no `is_featured` field, no API parameter, and no curation rule anywhere. Rather
 * than invent a merchandising flag and the schema change to carry it inside a page milestone, the
 * selection is derived from what the catalogue already says: the caller passes the priciest
 * products and this takes the first of each distinct category.
 *
 * Why one per category: variety. The seed inserts category by category, so a plain "newest four"
 * would be four Decor pieces in a row, and a plain "priciest four" would be two Bedroom and two
 * Living Room pieces. One per category is what makes the row read as a range rather than a corner.
 *
 * The argument is expected in the order it should be shown — price descending — so the result is
 * the priciest piece of each category, in the order those categories first appear.
 *
 * The honest consequence: this is a *derived* featured row, not an editorial one. The heading and
 * supporting line the page renders say so. If curation is ever wanted, it wants a real field and an
 * API filter, which is a backend task rather than a hidden change smuggled into a page.
 */
export function selectFeatured(
  products: ProductCard[],
  count: number = FEATURED_COUNT,
): ProductCard[] {
  const seen = new Set<string>();
  const picked: ProductCard[] = [];

  for (const product of products) {
    if (seen.has(product.category.slug)) {
      continue;
    }

    seen.add(product.category.slug);
    picked.push(product);

    if (picked.length === count) {
      break;
    }
  }

  return picked;
}

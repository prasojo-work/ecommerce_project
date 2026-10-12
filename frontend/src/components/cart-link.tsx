"use client";

import Link from "next/link";

import { unitsIn } from "@/lib/cart";

import { useCart } from "./cart-provider";
import { useSession } from "./session-provider";

/**
 * The header's cart entry, and the count `US-3.1` asks to update on an add.
 *
 * It renders for a signed-in shopper only: `ADR-0017` puts the cart behind a token, so offering one
 * to a signed-out visitor would be offering a sign-in page with extra steps. The count is text
 * rather than a coloured dot, because `SCOPE.md` NFR-2 forbids state carried by colour alone.
 *
 * During `restoring` it holds its own space instead of rendering — the same trick the session row
 * uses beside it. A link that appeared after the refresh would shift the header on every page load.
 */
export function CartLink() {
  const { status } = useSession();
  const { cart } = useCart();

  if (status !== "authenticated") {
    return status === "restoring" ? (
      <span className="inline-block h-5 min-w-16" aria-hidden="true" />
    ) : null;
  }

  const units = unitsIn(cart);

  return (
    <Link href="/cart" className="inline-flex min-h-11 items-center">
      Cart{units > 0 ? ` (${String(units)})` : ""}
    </Link>
  );
}

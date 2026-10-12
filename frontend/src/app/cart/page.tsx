import type { Metadata } from "next";

import { CartScreen } from "@/components/cart-screen";

export const metadata: Metadata = {
  title: "Your cart — LYSHEIM",
  description: "The pieces you have chosen, with a running total.",
};

/**
 * `/cart` (`UX.md` section 3, `US-3.4`). A Server Component for the heading and the frame — the same
 * split `/account` uses, and what lets the route carry its own title (`NFR-6`), which a client
 * component cannot.
 */
export default function CartPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="text-3xl tracking-tight">Your cart</h1>
      <CartScreen />
    </main>
  );
}

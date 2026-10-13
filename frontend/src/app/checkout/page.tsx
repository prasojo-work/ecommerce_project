import type { Metadata } from "next";

import { CheckoutScreen } from "@/components/checkout-screen";

export const metadata: Metadata = {
  title: "Checkout — LYSHEIM",
  description: "Delivery, shipping and payment, in four steps.",
};

/**
 * `/checkout` (`UX.md` section 4, `US-4.1`-`US-4.4`). A Server Component for the heading and the
 * frame — the split `/cart` uses, and what lets the route carry its own title (`NFR-6`), which a
 * client component cannot.
 */
export default function CheckoutPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="text-3xl tracking-tight">Checkout</h1>
      <CheckoutScreen />
    </main>
  );
}

import type { Metadata } from "next";

import { OrderHistoryScreen } from "@/components/order-history-screen";

export const metadata: Metadata = {
  title: "Your orders — LYSHEIM",
  description: "Every order you have placed, newest first.",
};

/**
 * `/orders` (`UX.md` flow E, `US-4.5`). A Server Component for the heading and the frame — the split
 * `/cart` and `/account` use — which is what lets the route carry its own title (`NFR-6`), something
 * a client component cannot. The list itself is the client's, because the token that reads it lives
 * only in memory (`ADR-0009`).
 */
export default function OrdersPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="text-3xl tracking-tight">Your orders</h1>
      <OrderHistoryScreen />
    </main>
  );
}

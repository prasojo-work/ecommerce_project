import type { Metadata } from "next";
import { Suspense } from "react";

import { OrderDetailScreen } from "@/components/order-detail-screen";

export const metadata: Metadata = {
  title: "Your order — LYSHEIM",
  description: "One order: its status, its lines, where it went, and how it reached that status.",
};

/**
 * `/orders/[number]` (`UX.md` flow E, `US-4.6`). A Server Component for the heading and the frame —
 * the split `/products/[slug]` uses. Reading `params` is request-time, so under Cache Components
 * (`next.config.ts`) the number is waited for inside the Suspense boundary below rather than in the
 * page body, which keeps the heading in the static shell while the order's own content streams. The
 * order is the client's to fetch, because the token that reads it lives only in memory (`ADR-0009`).
 */
export default function OrderPage(props: PageProps<"/orders/[number]">) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl tracking-tight">Your order</h1>
      <Suspense fallback={<p className="mt-10 text-muted">Loading…</p>}>
        <OrderDetail params={props.params} />
      </Suspense>
    </main>
  );
}

async function OrderDetail({ params }: Pick<PageProps<"/orders/[number]">, "params">) {
  const { number } = await params;
  return <OrderDetailScreen orderNumber={number} />;
}

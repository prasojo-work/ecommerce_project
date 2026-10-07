import { OrderDetailView } from "@/components/OrderDetailView";

type Params = { number: string };

export const metadata = { title: "Order" };

export default async function OrderPage({ params }: { params: Promise<Params> }) {
  const { number } = await params;
  return <OrderDetailView number={number} />;
}

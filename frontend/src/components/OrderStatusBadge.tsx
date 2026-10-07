import { orderStatusLabel, orderStatusTone } from "@/lib/orders";

export function OrderStatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${orderStatusTone(status)}`}
    >
      {orderStatusLabel(status)}
    </span>
  );
}

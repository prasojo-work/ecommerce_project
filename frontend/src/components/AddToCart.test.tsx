import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AddToCart } from "@/components/AddToCart";
import type { ProductVariant } from "@/lib/api";

const { add } = vi.hoisted(() => ({ add: vi.fn().mockResolvedValue(undefined) }));
const { push } = vi.hoisted(() => ({ push: vi.fn() }));
const { auth } = vi.hoisted(() => ({
  auth: { user: { id: 1, email: "a@b.co", full_name: "Shopper" }, ready: true },
}));

vi.mock("@/lib/cart", () => ({ useCart: () => ({ add }) }));
vi.mock("@/lib/auth", () => ({ useAuth: () => auth }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const variants: ProductVariant[] = [
  {
    id: 1,
    sku: "SOFA-A",
    name: "Fog grey",
    attributes: {},
    price: 4_200_000,
    stock_qty: 3,
    is_active: true,
  },
  {
    id: 2,
    sku: "SOFA-B",
    name: "Deep green",
    attributes: {},
    price: 4_900_000,
    stock_qty: 2,
    is_active: true,
  },
];

describe("AddToCart", () => {
  beforeEach(() => {
    add.mockClear();
    push.mockClear();
  });

  it("adds the first variant with quantity 1 by default", async () => {
    render(<AddToCart variants={variants} />);
    fireEvent.click(screen.getByRole("button", { name: /add to cart/i }));
    await waitFor(() => expect(add).toHaveBeenCalledWith(1, 1));
  });

  it("adds the selected variant and quantity", async () => {
    render(<AddToCart variants={variants} />);
    fireEvent.change(screen.getByLabelText("Option"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Quantity"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: /add to cart/i }));
    await waitFor(() => expect(add).toHaveBeenCalledWith(2, 3));
  });
});

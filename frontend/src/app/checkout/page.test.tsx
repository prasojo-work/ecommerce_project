import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CheckoutPage from "@/app/checkout/page";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

const { api } = vi.hoisted(() => ({
  api: {
    fetchAddresses: vi.fn(),
    fetchShippingOptions: vi.fn(),
    createOrder: vi.fn(),
    payWithMock: vi.fn(),
  },
}));

const { cartState } = vi.hoisted(() => ({
  cartState: {
    cart: null as unknown,
    count: 0,
    refresh: vi.fn(),
  },
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/api", () => api);
vi.mock("@/lib/cart", () => ({ useCart: () => cartState }));
vi.mock("@/lib/auth", () => ({
  useAuth: () => ({
    user: { id: 1, email: "shopper@example.com", full_name: "Shopper" },
    accessToken: "token-123",
    ready: true,
  }),
}));

beforeEach(() => {
  push.mockClear();
  cartState.refresh.mockClear();
  cartState.cart = {
    items: [
      {
        id: 1,
        variant_id: 1,
        product_title: "Nordvik Sofa",
        product_slug: "nordvik-sofa",
        variant_name: "Fog grey",
        image: null,
        unit_price: 1_000_000,
        quantity: 1,
        line_total: 1_000_000,
      },
    ],
    subtotal: 1_000_000,
    currency: "IDR",
  };

  api.fetchAddresses.mockResolvedValue([
    {
      id: 7,
      recipient: "Ada Lovelace",
      phone: "0812345678",
      line1: "Jl. Merdeka 1",
      line2: "",
      city: "Bandung",
      province: "West Java",
      postal_code: "40111",
      country: "ID",
      is_default: true,
    },
  ]);
  api.fetchShippingOptions.mockResolvedValue({
    subtotal: 1_000_000,
    currency: "IDR",
    free_shipping_threshold: 500_000,
    options: [
      { code: "standard", name: "Standard delivery", cost: 0, eta: "3–5 days" },
      { code: "express", name: "Express delivery", cost: 60_000, eta: "1–2 days" },
    ],
  });
  api.createOrder.mockResolvedValue({
    id: 1,
    number: "NDV-2026-000001",
    status: "pending_payment",
    subtotal: 1_000_000,
    shipping_cost: 0,
    total: 1_000_000,
    currency: "IDR",
    shipping_method: "standard",
    shipping_method_name: "Standard delivery",
    shipping_address: {},
    items: [],
    created_at: "2026-10-07T09:00:00Z",
  });
  api.payWithMock.mockResolvedValue({
    id: 1,
    order_number: "NDV-2026-000001",
    provider: "mock",
    status: "succeeded",
    amount: 1_000_000,
    provider_reference: "MOCK-ABC",
    created_at: "2026-10-07T09:00:00Z",
  });
});

describe("CheckoutPage", () => {
  it("shows the shipping options with their cost and ETA", async () => {
    render(<CheckoutPage />);

    expect(await screen.findByText("Standard delivery")).toBeInTheDocument();
    expect(screen.getByText("Express delivery")).toBeInTheDocument();
    expect(screen.getByText("3–5 days")).toBeInTheDocument();
    expect(screen.getByText("1–2 days")).toBeInTheDocument();
    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
  });

  it("places the order then pays, and lands on the order page", async () => {
    render(<CheckoutPage />);
    fireEvent.click(await screen.findByRole("radio", { name: /express/i }));
    fireEvent.click(screen.getByRole("button", { name: /pay/i }));

    await waitFor(() =>
      expect(api.createOrder).toHaveBeenCalledWith("token-123", {
        address_id: 7,
        shipping_method: "express",
        idempotency_key: expect.any(String),
      }),
    );
    expect(api.payWithMock).toHaveBeenCalledWith("token-123", "NDV-2026-000001", false);
    expect(cartState.refresh).toHaveBeenCalled();
    await waitFor(() => expect(push).toHaveBeenCalledWith("/orders/NDV-2026-000001"));
  });

  it("can simulate a declined payment for the demo", async () => {
    render(<CheckoutPage />);
    fireEvent.click(await screen.findByLabelText(/simulate a declined payment/i));
    fireEvent.click(screen.getByRole("button", { name: /pay/i }));

    await waitFor(() =>
      expect(api.payWithMock).toHaveBeenCalledWith("token-123", "NDV-2026-000001", true),
    );
  });

  it("surfaces an error when the order cannot be placed", async () => {
    api.createOrder.mockRejectedValue(new Error("Only 1 left of Nordvik Sofa."));
    render(<CheckoutPage />);
    fireEvent.click(await screen.findByRole("button", { name: /pay/i }));

    expect(await screen.findByText("Only 1 left of Nordvik Sofa.")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("asks for an address before it will take payment", async () => {
    api.fetchAddresses.mockResolvedValue([]);
    render(<CheckoutPage />);

    expect(await screen.findByText(/no saved address yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /pay/i })).toBeDisabled();
  });
});

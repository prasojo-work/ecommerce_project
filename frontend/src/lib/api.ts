export type Category = {
  id: number;
  name: string;
  slug: string;
};

export type ProductImage = {
  url: string;
  alt: string;
};

export type ProductVariant = {
  id: number;
  sku: string;
  name: string;
  attributes: Record<string, unknown>;
  price: number;
  stock_qty: number;
  is_active: boolean;
};

export type ProductListItem = {
  id: number;
  title: string;
  slug: string;
  category: Category;
  brand: string;
  price_from: number;
  currency: string;
  image: string | null;
};

export type ProductDetail = {
  id: number;
  title: string;
  slug: string;
  description: string;
  brand: string;
  category: Category;
  base_price: number;
  currency: string;
  images: ProductImage[];
  variants: ProductVariant[];
};

export type PaginatedProducts = {
  count: number;
  page: number;
  page_size: number;
  results: ProductListItem[];
};

export type ProductQuery = {
  q?: string;
  category?: string;
  sort?: string;
  page?: number;
  page_size?: number;
};

const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
const INTERNAL_API_URL = process.env.INTERNAL_API_URL ?? PUBLIC_API_URL;

function apiBaseUrl(): string {
  return typeof window === "undefined" ? INTERNAL_API_URL : PUBLIC_API_URL;
}

// Public catalog reads: safe to cache, and the API caches them too, so a repeat
// render is cheap. Per-user reads use `requestJson` below, which passes no cache
// option and so stays uncached.
const CATALOG_REVALIDATE_SECONDS = 60;

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    next: { revalidate: CATALOG_REVALIDATE_SECONDS, tags: ["catalog"] },
  });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}) for ${path}`);
  }
  return (await response.json()) as T;
}

export function fetchCategories(): Promise<Category[]> {
  return getJson<Category[]>("/categories");
}

export function fetchProducts(query: ProductQuery = {}): Promise<PaginatedProducts> {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.category) params.set("category", query.category);
  if (query.sort) params.set("sort", query.sort);
  if (query.page) params.set("page", String(query.page));
  if (query.page_size) params.set("page_size", String(query.page_size));
  const suffix = params.toString();
  return getJson<PaginatedProducts>(`/products${suffix ? `?${suffix}` : ""}`);
}

export async function fetchProduct(slug: string): Promise<ProductDetail | null> {
  const response = await fetch(`${apiBaseUrl()}/products/${slug}`, {
    next: { revalidate: CATALOG_REVALIDATE_SECONDS, tags: ["catalog"] },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return (await response.json()) as ProductDetail;
}

export type AuthTokens = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type CurrentUser = {
  id: number;
  email: string;
  full_name: string;
};

export type Address = {
  id: number;
  recipient: string;
  phone: string;
  line1: string;
  line2: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
  is_default: boolean;
};

export type AddressInput = Omit<Address, "id">;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "content-type": "application/json",
      ...(init.headers as Record<string, string> | undefined),
    },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  return (await response.json()) as T;
}

function bearer(accessToken: string): Record<string, string> {
  return { authorization: `Bearer ${accessToken}` };
}

export function registerUser(input: {
  email: string;
  password: string;
  full_name: string;
}): Promise<AuthTokens> {
  return requestJson<AuthTokens>("/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function loginUser(input: { email: string; password: string }): Promise<AuthTokens> {
  return requestJson<AuthTokens>("/auth/login", { method: "POST", body: JSON.stringify(input) });
}

/**
 * Restores a session from the httpOnly refresh cookie.
 *
 * Resolves to `null` when this browser has no session — the API answers 204 rather
 * than 401, because "no refresh cookie" is a normal state for an anonymous visitor
 * and a 401 logs a browser console error on every first visit.
 *
 * Deliberately not `requestJson`: no body means no `content-type`, which keeps the
 * request "simple" and avoids a CORS preflight.
 */
export async function refreshSession(): Promise<AuthTokens | null> {
  const response = await fetch(`${apiBaseUrl()}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  return (await response.json()) as AuthTokens;
}

export function fetchMe(accessToken: string): Promise<CurrentUser> {
  return requestJson<CurrentUser>("/auth/me", { headers: bearer(accessToken) });
}

export async function logoutUser(): Promise<void> {
  await fetch(`${apiBaseUrl()}/auth/logout`, { method: "POST", credentials: "include" });
}

export function fetchAddresses(accessToken: string): Promise<Address[]> {
  return requestJson<Address[]>("/addresses", { headers: bearer(accessToken) });
}

export function createAddress(accessToken: string, input: AddressInput): Promise<Address> {
  return requestJson<Address>("/addresses", {
    method: "POST",
    headers: bearer(accessToken),
    body: JSON.stringify(input),
  });
}

export async function deleteAddress(accessToken: string, id: number): Promise<void> {
  await fetch(`${apiBaseUrl()}/addresses/${id}`, {
    method: "DELETE",
    credentials: "include",
    headers: bearer(accessToken),
  });
}

export type CartItem = {
  id: number;
  variant_id: number;
  product_title: string;
  product_slug: string;
  variant_name: string;
  image: string | null;
  unit_price: number;
  quantity: number;
  line_total: number;
};

export type Cart = {
  items: CartItem[];
  subtotal: number;
  currency: string;
};

export function fetchCart(accessToken: string): Promise<Cart> {
  return requestJson<Cart>("/cart", { headers: bearer(accessToken) });
}

export function addCartItem(
  accessToken: string,
  variantId: number,
  quantity: number,
): Promise<Cart> {
  return requestJson<Cart>("/cart/items", {
    method: "POST",
    headers: bearer(accessToken),
    body: JSON.stringify({ variant_id: variantId, quantity }),
  });
}

export function updateCartItem(
  accessToken: string,
  itemId: number,
  quantity: number,
): Promise<Cart> {
  return requestJson<Cart>(`/cart/items/${itemId}`, {
    method: "PATCH",
    headers: bearer(accessToken),
    body: JSON.stringify({ quantity }),
  });
}

export function removeCartItem(accessToken: string, itemId: number): Promise<Cart> {
  return requestJson<Cart>(`/cart/items/${itemId}`, {
    method: "DELETE",
    headers: bearer(accessToken),
  });
}

export type ShippingOption = {
  code: string;
  name: string;
  cost: number;
  eta: string;
};

export type ShippingOptions = {
  subtotal: number;
  currency: string;
  free_shipping_threshold: number;
  options: ShippingOption[];
};

export type OrderStatus =
  | "pending_payment"
  | "paid"
  | "processing"
  | "shipped"
  | "completed"
  | "cancelled";

export type OrderItem = {
  id: number;
  variant_id: number | null;
  product_title: string;
  variant_name: string;
  unit_price: number;
  quantity: number;
  line_total: number;
};

export type OrderAddress = {
  recipient: string;
  phone: string;
  line1: string;
  line2: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
};

export type Order = {
  id: number;
  number: string;
  status: OrderStatus;
  subtotal: number;
  shipping_cost: number;
  total: number;
  currency: string;
  shipping_method: string;
  shipping_method_name: string;
  shipping_address: OrderAddress;
  items: OrderItem[];
  created_at: string;
};

export type OrderSummary = {
  id: number;
  number: string;
  status: OrderStatus;
  total: number;
  currency: string;
  item_count: number;
  created_at: string;
};

export type PaginatedOrders = {
  count: number;
  page: number;
  page_size: number;
  results: OrderSummary[];
};

export type OrderInput = {
  address_id: number;
  shipping_method: string;
  idempotency_key: string;
};

export type PaymentStatus = "initiated" | "succeeded" | "failed" | "refunded";

export type Payment = {
  id: number;
  order_number: string;
  provider: string;
  status: PaymentStatus;
  amount: number;
  provider_reference: string;
  created_at: string;
};

export function fetchShippingOptions(accessToken: string): Promise<ShippingOptions> {
  return requestJson<ShippingOptions>("/shipping/options", {
    headers: bearer(accessToken),
  });
}

export function createOrder(accessToken: string, input: OrderInput): Promise<Order> {
  return requestJson<Order>("/orders", {
    method: "POST",
    headers: bearer(accessToken),
    body: JSON.stringify(input),
  });
}

export function fetchOrders(accessToken: string): Promise<PaginatedOrders> {
  return requestJson<PaginatedOrders>("/orders", { headers: bearer(accessToken) });
}

export function fetchOrder(accessToken: string, number: string): Promise<Order> {
  return requestJson<Order>(`/orders/${number}`, { headers: bearer(accessToken) });
}

export function payWithMock(
  accessToken: string,
  orderNumber: string,
  simulateFailure = false,
): Promise<Payment> {
  return requestJson<Payment>("/payments/mock", {
    method: "POST",
    headers: bearer(accessToken),
    body: JSON.stringify({
      order_number: orderNumber,
      simulate_failure: simulateFailure,
    }),
  });
}

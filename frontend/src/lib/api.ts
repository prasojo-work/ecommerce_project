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

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, { cache: "no-store" });
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
    next: { revalidate: 60 },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return (await response.json()) as ProductDetail;
}

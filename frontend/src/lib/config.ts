const DEFAULT_API_BASE_URL = "http://localhost:8000";

/** Base URL of the LYSHEIM API, from `NEXT_PUBLIC_API_BASE_URL`. */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configured ? configured : DEFAULT_API_BASE_URL;
}

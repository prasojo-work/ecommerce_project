import { afterEach, describe, expect, it, vi } from "vitest";

import { getApiBaseUrl } from "./config";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("getApiBaseUrl", () => {
  it("falls back to the local API when unset", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");

    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("uses the configured value when present", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");

    expect(getApiBaseUrl()).toBe("https://api.example.com");
  });
});

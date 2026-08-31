import { describe, expect, it, vi } from "vitest";
import { fetchHealth, resolveApiBase } from "./api";

describe("resolveApiBase", () => {
  it("falls back to localhost when VITE_API_BASE is unset", () => {
    expect(resolveApiBase({})).toBe("http://localhost:8000");
  });

  it("uses VITE_API_BASE when set", () => {
    expect(resolveApiBase({ VITE_API_BASE: "http://api.internal" })).toBe(
      "http://api.internal",
    );
  });
});

describe("fetchHealth", () => {
  it("returns the status from a healthy response", async () => {
    const fakeFetch = vi.fn(async () => new Response(JSON.stringify({ status: "ok" }), {
      status: 200,
    }));

    await expect(fetchHealth("http://api.internal", fakeFetch as typeof fetch)).resolves.toBe(
      "ok",
    );
    expect(fakeFetch).toHaveBeenCalledWith("http://api.internal/health");
  });

  it("throws when the backend responds with an error status", async () => {
    const fakeFetch = vi.fn(async () => new Response("", { status: 503 }));

    await expect(
      fetchHealth("http://api.internal", fakeFetch as typeof fetch),
    ).rejects.toThrow("503");
  });
});

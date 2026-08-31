import { describe, expect, it, vi } from "vitest";
import { askChat, fetchHealth, resolveApiBase } from "./api";

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

describe("askChat", () => {
  it("posts the question and returns the answer with citations", async () => {
    const fakeFetch = vi.fn(async () =>
      new Response(
        JSON.stringify({
          answer: "Dr. Elena Vasquez",
          citations: [
            { document_id: "policy-1", document_title: "Software Change Management Policy" },
          ],
        }),
        { status: 200 },
      ),
    );

    const result = await askChat(
      "http://api.internal",
      "Who is the approving authority?",
      fakeFetch as typeof fetch,
    );

    expect(result.answer).toBe("Dr. Elena Vasquez");
    expect(result.citations).toEqual([
      { document_id: "policy-1", document_title: "Software Change Management Policy" },
    ]);
    expect(fakeFetch).toHaveBeenCalledWith(
      "http://api.internal/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "Who is the approving authority?" }),
      }),
    );
  });

  it("throws when the backend responds with an error status", async () => {
    const fakeFetch = vi.fn(async () => new Response("", { status: 500 }));

    await expect(
      askChat("http://api.internal", "irrelevant", fakeFetch as typeof fetch),
    ).rejects.toThrow("500");
  });
});

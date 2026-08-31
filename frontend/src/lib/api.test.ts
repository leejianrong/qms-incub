import { describe, expect, it, vi } from "vitest";
import { askChat, fetchDocuments, fetchHealth, resolveApiBase, startBatch } from "./api";

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

describe("startBatch", () => {
  it("posts batch options and returns the started response", async () => {
    const fakeFetch = vi.fn(async () =>
      new Response(JSON.stringify({ status: "started", count: 5 }), { status: 200 }),
    );

    const result = await startBatch(
      "http://api.internal",
      { count: 5, seed: 42 },
      fakeFetch as typeof fetch,
    );

    expect(result).toEqual({ status: "started", count: 5 });
    expect(fakeFetch).toHaveBeenCalledWith(
      "http://api.internal/documents/batch",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ count: 5, seed: 42 }),
      }),
    );
  });

  it("throws when the backend responds with an error status", async () => {
    const fakeFetch = vi.fn(async () => new Response("", { status: 500 }));

    await expect(
      startBatch("http://api.internal", { count: 5, seed: 0 }, fakeFetch as typeof fetch),
    ).rejects.toThrow("500");
  });
});

describe("fetchDocuments", () => {
  it("returns the document status list", async () => {
    const documents = [
      {
        id: "synthetic-0001",
        title: "Synthetic Policy Document 1",
        origin: "generated",
        is_synthetic: true,
        status: "embedded",
        chunk_count: 2,
        error: null,
      },
    ];
    const fakeFetch = vi.fn(async () => new Response(JSON.stringify(documents), { status: 200 }));

    const result = await fetchDocuments("http://api.internal", fakeFetch as typeof fetch);

    expect(result).toEqual(documents);
    expect(fakeFetch).toHaveBeenCalledWith("http://api.internal/documents");
  });

  it("throws when the backend responds with an error status", async () => {
    const fakeFetch = vi.fn(async () => new Response("", { status: 500 }));

    await expect(
      fetchDocuments("http://api.internal", fakeFetch as typeof fetch),
    ).rejects.toThrow("500");
  });
});

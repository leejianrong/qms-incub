import { describe, expect, it, vi } from "vitest";
import {
  askChat,
  createProject,
  fetchHealth,
  getProject,
  resolveApiBase,
  uploadArtifact,
} from "./api";

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

describe("createProject", () => {
  it("posts the wizard answers and returns the generated project + todos", async () => {
    const fakeFetch = vi.fn(async () =>
      new Response(
        JSON.stringify({
          project: { id: "proj-1", name: "Customer Portal", risk_tier: "high" },
          todos: [
            {
              id: "todo-1",
              project_id: "proj-1",
              requirement_id: "req-1",
              requirement_description: "External security audit",
              clause_text: "Clause 1",
              standard_name: "Change Management",
              status: "pending",
            },
          ],
        }),
        { status: 201 },
      ),
    );

    const result = await createProject(
      "http://api.internal",
      "Customer Portal",
      { data_sensitivity_high: true, customer_facing: true, regulatory_exposure: true },
      fakeFetch as typeof fetch,
    );

    expect(result.project.risk_tier).toBe("high");
    expect(result.todos).toHaveLength(1);
    expect(fakeFetch).toHaveBeenCalledWith(
      "http://api.internal/projects",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          name: "Customer Portal",
          answers: {
            data_sensitivity_high: true,
            customer_facing: true,
            regulatory_exposure: true,
          },
        }),
      }),
    );
  });
});

describe("getProject", () => {
  it("fetches a project's todos by id", async () => {
    const fakeFetch = vi.fn(async () =>
      new Response(
        JSON.stringify({
          project: { id: "proj-1", name: "Customer Portal", risk_tier: "low" },
          todos: [],
        }),
        { status: 200 },
      ),
    );

    const result = await getProject("http://api.internal", "proj-1", fakeFetch as typeof fetch);

    expect(result.project.id).toBe("proj-1");
    expect(fakeFetch).toHaveBeenCalledWith("http://api.internal/projects/proj-1");
  });
});

describe("uploadArtifact", () => {
  it("posts the file as multipart form data and returns the self-attested todo", async () => {
    const fakeFetch = vi.fn(async () =>
      new Response(
        JSON.stringify({
          artifact: { id: "art-1", todo_item_id: "todo-1", filename: "evidence.pdf" },
          todo: {
            id: "todo-1",
            project_id: "proj-1",
            requirement_id: "req-1",
            requirement_description: "Upload proof of testing",
            clause_text: "Clause 1",
            standard_name: "Change Management",
            status: "complied",
          },
        }),
        { status: 201 },
      ),
    );

    const file = new File(["fake pdf bytes"], "evidence.pdf", { type: "application/pdf" });
    const result = await uploadArtifact(
      "http://api.internal",
      "todo-1",
      file,
      fakeFetch as typeof fetch,
    );

    expect(result.todo.status).toBe("complied");
    expect(fakeFetch).toHaveBeenCalledWith(
      "http://api.internal/todos/todo-1/artifacts",
      expect.objectContaining({ method: "POST" }),
    );
    const init = (fakeFetch.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(init.body).toBeInstanceOf(FormData);
  });

  it("throws when the backend responds with an error status", async () => {
    const fakeFetch = vi.fn(async () => new Response("", { status: 404 }));
    const file = new File(["x"], "evidence.pdf");

    await expect(
      uploadArtifact("http://api.internal", "missing", file, fakeFetch as typeof fetch),
    ).rejects.toThrow("404");
  });
});

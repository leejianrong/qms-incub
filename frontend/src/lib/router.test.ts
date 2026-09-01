import { describe, expect, it } from "vitest";
import { pathOf, paramOf } from "./router.svelte";

describe("pathOf", () => {
  it("returns the pathname unchanged when there is no query string", () => {
    expect(pathOf("/project")).toBe("/project");
  });

  it("strips the query string", () => {
    expect(pathOf("/project?id=abc-123")).toBe("/project");
  });

  it("handles root", () => {
    expect(pathOf("/")).toBe("/");
  });
});

describe("paramOf", () => {
  it("reads a query parameter", () => {
    expect(paramOf("/project?id=abc-123", "id")).toBe("abc-123");
  });

  it("returns null when the parameter is absent", () => {
    expect(paramOf("/project?id=abc-123", "missing")).toBeNull();
  });

  it("returns null when there is no query string at all", () => {
    expect(paramOf("/project", "id")).toBeNull();
  });

  it("decodes URL-encoded values", () => {
    expect(paramOf("/project?id=abc%20123", "id")).toBe("abc 123");
  });
});

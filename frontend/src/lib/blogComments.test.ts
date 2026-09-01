import { describe, expect, it } from "vitest";
import { commentCount, getComments, postComment } from "./blogComments.svelte";

describe("blogComments", () => {
  it("starts empty for a post with no comments", () => {
    expect(getComments("unused-post-1")).toEqual([]);
    expect(commentCount("unused-post-1")).toBe(0);
  });

  it("appends a comment and keeps it scoped to its post", () => {
    postComment("post-a", "Kim Alvarez", "Project manager", "Great write-up.");
    expect(getComments("post-a")).toHaveLength(1);
    expect(getComments("post-a")[0]).toMatchObject({
      who: "Kim Alvarez",
      role: "Project manager",
      text: "Great write-up.",
    });
    expect(getComments("post-b")).toEqual([]);
  });

  it("appends in order and updates the count", () => {
    postComment("post-c", "Kim Alvarez", "Project manager", "First note");
    postComment("post-c", "Kim Alvarez", "Project manager", "Second note");
    expect(getComments("post-c").map((c) => c.text)).toEqual(["First note", "Second note"]);
    expect(commentCount("post-c")).toBe(2);
  });

  it("ignores a blank or whitespace-only comment", () => {
    postComment("post-d", "Kim Alvarez", "Project manager", "   ");
    expect(getComments("post-d")).toEqual([]);
  });

  it("trims surrounding whitespace from a posted comment", () => {
    postComment("post-e", "Kim Alvarez", "Project manager", "  padded  ");
    expect(getComments("post-e")[0].text).toBe("padded");
  });
});

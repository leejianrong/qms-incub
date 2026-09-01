import { describe, expect, it } from "vitest";
import { commentCount, getComments, postComment } from "./discussionState.svelte";

describe("discussionState", () => {
  it("starts empty for a todo with no comments", () => {
    expect(getComments("unused-todo-1")).toEqual([]);
    expect(commentCount("unused-todo-1")).toBe(0);
  });

  it("appends a comment and keeps it scoped to its todo", () => {
    postComment("todo-a", "Kim Alvarez", "Project manager", "Attaching the updated evidence.");
    expect(getComments("todo-a")).toHaveLength(1);
    expect(getComments("todo-a")[0]).toMatchObject({
      who: "Kim Alvarez",
      role: "Project manager",
      text: "Attaching the updated evidence.",
    });
    expect(getComments("todo-b")).toEqual([]);
  });

  it("appends in order and updates the count", () => {
    postComment("todo-c", "Kim Alvarez", "Project manager", "First note");
    postComment("todo-c", "Kim Alvarez", "Project manager", "Second note");
    expect(getComments("todo-c").map((c) => c.text)).toEqual(["First note", "Second note"]);
    expect(commentCount("todo-c")).toBe(2);
  });

  it("ignores a blank or whitespace-only comment", () => {
    postComment("todo-d", "Kim Alvarez", "Project manager", "   ");
    expect(getComments("todo-d")).toEqual([]);
  });

  it("trims surrounding whitespace from a posted comment", () => {
    postComment("todo-e", "Kim Alvarez", "Project manager", "  padded  ");
    expect(getComments("todo-e")[0].text).toBe("padded");
  });
});

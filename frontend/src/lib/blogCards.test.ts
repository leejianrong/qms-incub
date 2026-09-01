import { describe, expect, it } from "vitest";
import {
  deriveExcerpt,
  favoritedPosts,
  formatPublishedAt,
  matchesBlogSearch,
  paragraphsOf,
  publishedPosts,
  sortByRecency,
} from "./blogCards";
import type { BlogPost } from "./api";

function post(overrides: Partial<BlogPost> = {}): BlogPost {
  return {
    id: "b1",
    title: "Closing out the design review",
    body: "We wrapped the design review a week early.",
    published_at: "2026-08-20T10:00:00Z",
    chunk_count: 4,
    ...overrides,
  };
}

describe("publishedPosts", () => {
  it("keeps only posts with a published_at", () => {
    const posts = [post({ id: "a", published_at: "2026-08-01T00:00:00Z" }), post({ id: "b", published_at: null })];
    expect(publishedPosts(posts).map((p) => p.id)).toEqual(["a"]);
  });
});

describe("sortByRecency", () => {
  it("orders most-recently-published first", () => {
    const posts = [
      post({ id: "old", published_at: "2026-01-01T00:00:00Z" }),
      post({ id: "new", published_at: "2026-08-01T00:00:00Z" }),
      post({ id: "mid", published_at: "2026-04-01T00:00:00Z" }),
    ];
    expect(sortByRecency(posts).map((p) => p.id)).toEqual(["new", "mid", "old"]);
  });

  it("does not mutate the input array", () => {
    const posts = [post({ id: "a" }), post({ id: "b" })];
    const original = [...posts];
    sortByRecency(posts);
    expect(posts).toEqual(original);
  });

  it("sorts unpublished (null) posts as oldest", () => {
    const posts = [post({ id: "draft", published_at: null }), post({ id: "live", published_at: "2026-01-01T00:00:00Z" })];
    expect(sortByRecency(posts).map((p) => p.id)).toEqual(["live", "draft"]);
  });
});

describe("formatPublishedAt", () => {
  it("formats an ISO datetime as a short UTC date", () => {
    expect(formatPublishedAt("2026-08-20T10:00:00Z")).toBe("Aug 20, 2026");
  });

  it("falls back to a placeholder for null", () => {
    expect(formatPublishedAt(null)).toBe("Unpublished");
  });

  it("falls back to a placeholder for an unparseable value", () => {
    expect(formatPublishedAt("not a date")).toBe("Unpublished");
  });
});

describe("deriveExcerpt", () => {
  it("returns the whole body when under the limit", () => {
    expect(deriveExcerpt("Short body.")).toBe("Short body.");
  });

  it("collapses whitespace before measuring", () => {
    expect(deriveExcerpt("  a   b  \n\n c  ")).toBe("a b c");
  });

  it("cuts at a word boundary and appends an ellipsis when over the limit", () => {
    const body = "word ".repeat(50).trim();
    const excerpt = deriveExcerpt(body, 20);
    expect(excerpt.endsWith("…")).toBe(true);
    expect(excerpt.length).toBeLessThanOrEqual(21);
    expect(excerpt.endsWith(" …")).toBe(false);
  });

  it("handles a single very long word with no boundary to cut at", () => {
    const body = "a".repeat(30);
    const excerpt = deriveExcerpt(body, 10);
    expect(excerpt).toBe("a".repeat(10) + "…");
  });
});

describe("paragraphsOf", () => {
  it("splits on blank lines", () => {
    expect(paragraphsOf("Para one.\n\nPara two.\n\nPara three.")).toEqual([
      "Para one.",
      "Para two.",
      "Para three.",
    ]);
  });

  it("returns a single paragraph when there are no blank-line breaks", () => {
    expect(paragraphsOf("One line.\nStill the same paragraph.")).toEqual(["One line.\nStill the same paragraph."]);
  });

  it("returns an empty array for an empty body", () => {
    expect(paragraphsOf("")).toEqual([]);
  });

  it("ignores extra blank lines between paragraphs", () => {
    expect(paragraphsOf("A.\n\n\n\nB.")).toEqual(["A.", "B."]);
  });
});

describe("matchesBlogSearch", () => {
  it("matches on title case-insensitively", () => {
    expect(matchesBlogSearch(post({ title: "Design Review Notes" }), "design")).toBe(true);
  });

  it("matches on body", () => {
    expect(matchesBlogSearch(post({ body: "The retention policy changed." }), "retention")).toBe(true);
  });

  it("blank query matches everything", () => {
    expect(matchesBlogSearch(post(), "   ")).toBe(true);
  });

  it("returns false when neither title nor body match", () => {
    expect(matchesBlogSearch(post({ title: "Design review", body: "Nothing relevant." }), "payroll")).toBe(false);
  });
});

describe("favoritedPosts", () => {
  it("keeps only posts present in the favourite id map", () => {
    const posts = [post({ id: "a" }), post({ id: "b" }), post({ id: "c" })];
    expect(favoritedPosts(posts, { b: true }).map((p) => p.id)).toEqual(["b"]);
  });

  it("returns an empty array when nothing is favourited", () => {
    expect(favoritedPosts([post()], {})).toEqual([]);
  });
});

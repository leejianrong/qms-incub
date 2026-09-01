import { describe, expect, it } from "vitest";
import { publishedFaqEntries } from "./faqCards";
import type { FAQEntry } from "./api";

function entry(overrides: Partial<FAQEntry> = {}): FAQEntry {
  return {
    id: "f1",
    question: "How long do approvals take?",
    answer: "Each approval sub-step shows its target turnaround.",
    published_at: "2026-08-20T10:00:00Z",
    chunk_count: 2,
    ...overrides,
  };
}

describe("publishedFaqEntries", () => {
  it("keeps only entries with a published_at", () => {
    const entries = [entry({ id: "a", published_at: "2026-08-01T00:00:00Z" }), entry({ id: "b", published_at: null })];
    expect(publishedFaqEntries(entries).map((e) => e.id)).toEqual(["a"]);
  });

  it("returns an empty array when nothing is published", () => {
    expect(publishedFaqEntries([entry({ published_at: null })])).toEqual([]);
  });

  it("returns an empty array for an empty input", () => {
    expect(publishedFaqEntries([])).toEqual([]);
  });

  it("does not mutate the input array", () => {
    const entries = [entry({ id: "a" }), entry({ id: "b", published_at: null })];
    const original = [...entries];
    publishedFaqEntries(entries);
    expect(entries).toEqual(original);
  });
});

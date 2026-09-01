// V18 step 5: pure, unit-tested view-model logic for the PM-facing Blog
// list/detail view — mirrors ui-reference/'s blogRest()/hero computation,
// but adapted to our real BlogPost shape ({ id, title, body, published_at,
// chunk_count }, see api.ts) rather than the reference's richer fictional
// model (author, kicker/topic, read time, excerpt, pull-quote, multi-
// paragraph body array). None of those fields exist in our data model, so
// this deliberately never fabricates them — only excerpt/paragraph/date
// derivations of the real title/body/published_at fields. Kept out of
// Blog.svelte so the derivation logic is testable without rendering, same
// pattern as projectCards.ts.
import type { BlogPost } from "./api";

// Draft posts (published_at === null) are authoring state in the
// BlogFaqEditor.svelte admin tool — they're never chunked/embedded into
// the corpus (V6's publish step, ADR-0012) and the PM-facing Blog view
// should only ever show what's actually published, same rule as the
// corpus itself.
export function publishedPosts(posts: BlogPost[]): BlogPost[] {
  return posts.filter((post) => post.published_at !== null);
}

export function sortByRecency(posts: BlogPost[]): BlogPost[] {
  return posts.slice().sort((a, b) => {
    const at = a.published_at ? Date.parse(a.published_at) : 0;
    const bt = b.published_at ? Date.parse(b.published_at) : 0;
    return bt - at;
  });
}

export function formatPublishedAt(publishedAt: string | null): string {
  if (!publishedAt) return "Unpublished";
  const date = new Date(publishedAt);
  if (Number.isNaN(date.getTime())) return "Unpublished";
  // Fixed to UTC rather than the viewer's local timezone, same reasoning
  // as projectCards.ts's formatSlaTarget — deterministic regardless of
  // where the viewer (or a test runner) happens to be.
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
}

// First ~160 chars of the body, collapsed to single spaces and cut at a
// word boundary — stands in for the reference's hand-authored `excerpt`
// field, which we don't have.
export function deriveExcerpt(body: string, maxLen = 160): string {
  const collapsed = body.trim().replace(/\s+/g, " ");
  if (collapsed.length <= maxLen) return collapsed;
  const cut = collapsed.slice(0, maxLen).replace(/\s+\S*$/, "");
  return `${cut || collapsed.slice(0, maxLen)}…`;
}

// Splits on blank lines for paragraph rendering in the detail view. A
// body with no blank-line breaks comes back as a single paragraph rather
// than one line per newline, so plain single-newline text doesn't get
// fragmented.
export function paragraphsOf(body: string): string[] {
  const paras = body
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);
  return paras.length > 0 ? paras : [];
}

export function matchesBlogSearch(post: BlogPost, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (post.title + " " + post.body).toLowerCase().includes(q);
}

export function favoritedPosts(posts: BlogPost[], favoriteIds: Record<string, true>): BlogPost[] {
  return posts.filter((post) => !!favoriteIds[post.id]);
}

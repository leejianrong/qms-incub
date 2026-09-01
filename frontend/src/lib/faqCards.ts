// V18 step 6: pure, unit-tested view-model logic for the PM-facing FAQ
// accordion view — mirrors ui-reference/'s isFaq branch (a flat list of
// question rows that expand in place), adapted to our real FAQEntry shape
// ({ id, question, answer, published_at, chunk_count }, see api.ts) rather
// than the reference's fictional model, which groups entries by a
// hardcoded `group` field ("Approvals", "Process", "Evidence", "People")
// with no counterpart in our data. That grouping is never fabricated here
// — this renders a flat list, ordered as the backend returns it
// (created_at desc, see content/repository.py's list_faqs). Kept out of
// Faq.svelte so the derivation logic is testable without rendering, same
// pattern as blogCards.ts/projectCards.ts.
import type { FAQEntry } from "./api";

// Draft entries (published_at === null) are authoring state in the
// BlogFaqEditor.svelte admin tool — they're never chunked/embedded into
// the corpus (V6's publish step, ADR-0012) and the PM-facing FAQ view
// should only ever show what's actually published, same rule blogCards.ts's
// publishedPosts already applies to the Blog view.
export function publishedFaqEntries(entries: FAQEntry[]): FAQEntry[] {
  return entries.filter((entry) => entry.published_at !== null);
}

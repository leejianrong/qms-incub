<script lang="ts">
  // V18 step 6: the PM-facing FAQ accordion view, replacing the stub
  // Console.svelte used to render for the "faq" route. Consumes V6's
  // existing listFAQEntries endpoint — no new backend work. Layout follows
  // ui-reference/QMS Console.dc.html's isFaq branch (question list + a
  // "still stuck?" sidebar), but flattened: the reference groups entries
  // by a hardcoded `group` field ("Approvals"/"Process"/"Evidence"/
  // "People") that has no counterpart in our real FAQEntry shape
  // (question/answer/published_at only — see faqCards.ts), so this
  // renders one flat list rather than inventing categories. The
  // reference's "Contact step owner" button opens a chat drawer that's
  // explicitly out of scope for this slice (SLICES.md's V18 build plan);
  // the sidebar here just points PMs at a todo's Discussion thread
  // instead (V18 step 4, ProjectDetail.svelte) rather than wiring a
  // non-functional button.
  import PlusIcon from "@lucide/svelte/icons/plus";
  import MinusIcon from "@lucide/svelte/icons/minus";
  import { resolveApiBase, listFAQEntries, type FAQEntry } from "$lib/api";
  import { publishedFaqEntries } from "$lib/faqCards";

  const apiBase = resolveApiBase(import.meta.env);

  let entries = $state<FAQEntry[] | null>(null);
  let error = $state<string | null>(null);

  // Multiple entries can be open at once (a Record of id -> open), rather
  // than the reference's single-item-open behavior — simpler to implement
  // and reason about, and still matches the reference's core interaction
  // (click a question row, its answer expands in place, click again to
  // collapse) closely enough per the slice brief.
  let openIds = $state<Record<string, boolean>>({});

  async function load() {
    error = null;
    try {
      entries = await listFAQEntries(apiBase);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }

  load();

  const visibleEntries = $derived(entries === null ? [] : publishedFaqEntries(entries));

  function toggle(id: string) {
    openIds[id] = !openIds[id];
  }
</script>

<main class="mx-auto max-w-6xl p-8">
  <header class="space-y-1 border-b border-border pb-6">
    <div class="text-[10px] tracking-widest text-primary uppercase">FAQ</div>
    <h1 class="mt-1 text-4xl">Questions we get weekly</h1>
  </header>

  {#if error}
    <p class="mt-6 text-sm text-destructive">Error: {error}</p>
  {:else if entries === null}
    <p class="mt-6 text-sm text-muted-foreground">Loading FAQ entries…</p>
  {:else if visibleEntries.length === 0}
    <div class="mt-6 flex flex-col items-center gap-2 rounded-2xl border border-border bg-card py-14 text-center shadow-sm">
      <p class="text-sm text-muted-foreground">No FAQ entries published yet.</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 gap-0 lg:grid-cols-[minmax(0,1fr)_300px]">
      <section class="lg:border-r lg:border-border lg:pr-8">
        {#each visibleEntries as entry (entry.id)}
          <div class="border-b border-border">
            <button
              type="button"
              onclick={() => toggle(entry.id)}
              aria-expanded={!!openIds[entry.id]}
              class="flex w-full items-baseline gap-4 py-4 text-left"
            >
              <span class="flex-1 font-heading text-[16.5px] font-medium">{entry.question}</span>
              <span class="flex-none text-primary">
                {#if openIds[entry.id]}
                  <MinusIcon class="size-[18px]" />
                {:else}
                  <PlusIcon class="size-[18px]" />
                {/if}
              </span>
            </button>
            {#if openIds[entry.id]}
              <p class="max-w-[76ch] pb-5 text-[14.5px] leading-relaxed text-muted-foreground">{entry.answer}</p>
            {/if}
          </div>
        {/each}
      </section>

      <aside class="pt-2 pb-14 lg:pl-6">
        <h4 class="font-heading text-base font-medium">Still stuck?</h4>
        <p class="mt-2.5 text-[13px] leading-relaxed text-muted-foreground">
          Every todo names its owner and carries a Discussion thread. Comment there rather than emailing — the
          thread stays attached to the evidence.
        </p>
      </aside>
    </div>
  {/if}
</main>

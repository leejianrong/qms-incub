<script lang="ts">
  // V18 step 2: rework the plain project list into ui-reference/'s richer
  // dashboard — a stats strip, then a searchable/filterable/sortable card
  // grid with per-todo progress cells and an awaiting-approval/rework
  // alert. View-model derivation lives in lib/projectCards.ts so it's
  // unit-tested without rendering; this component is just data-fetching
  // and markup.
  import { Button } from "$lib/components/ui/button/index.js";
  import StarIcon from "@lucide/svelte/icons/star";
  import {
    resolveApiBase,
    listProjects,
    listProcessSteps,
    getProject,
    type Project,
    type TodoItem,
  } from "$lib/api";
  import {
    buildProjectCard,
    computeStats,
    matchesFilter,
    matchesSearch,
    sortCards,
    FILTER_KEYS,
    SORT_OPTIONS,
    type ProjectCardViewModel,
    type ProjectFilterKey,
    type ProjectSortKey,
  } from "$lib/projectCards";
  import { goToProject, isProjectFavorited, toggleFavoriteProject } from "$lib/consoleState.svelte";
  import { navigate } from "$lib/router.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  let cards = $state<ProjectCardViewModel[] | null>(null);
  let allTodos = $state<TodoItem[]>([]);
  let error = $state<string | null>(null);
  let query = $state("");
  let filter = $state<ProjectFilterKey>("All");
  let sort = $state<ProjectSortKey>("status");

  async function load() {
    error = null;
    try {
      const [projects, steps] = await Promise.all([listProjects(apiBase), listProcessSteps(apiBase)]);
      const details = await Promise.all(
        projects.map(async (project: Project) => {
          if (project.risk_tier === null) return { project, todos: [] as TodoItem[] };
          try {
            const detail = await getProject(apiBase, project.id);
            return { project, todos: detail.todos };
          } catch {
            return { project, todos: [] as TodoItem[] };
          }
        }),
      );
      allTodos = details.flatMap((d) => d.todos);
      cards = details.map((d) => buildProjectCard(d.project, d.todos, steps));
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }

  load();

  const stats = $derived.by(() => {
    const list = cards;
    if (list === null) return null;
    const s = computeStats(list, allTodos);
    return [
      { label: "My projects", value: s.totalProjects, note: "Under QMS Rev. 4.2" },
      {
        label: "Out for approval",
        value: s.outForApproval,
        note: s.outForApproval ? "Waiting on an approver" : "Nothing submitted",
      },
      {
        label: "Needs rework",
        value: s.needsRework,
        note: s.needsRework ? "Returned — evidence to redo" : "Nothing returned",
        hot: s.needsRework > 0,
      },
      { label: "Fully complied", value: s.fullyComplied, note: `of ${s.totalProjects} projects` },
    ];
  });

  const filterCounts = $derived.by(() => {
    const list = cards;
    if (list === null) return null;
    return FILTER_KEYS.map((key) => ({
      key,
      count: list.filter((c) => matchesSearch(c, query) && matchesFilter(c, key)).length,
    }));
  });

  const shownCards = $derived.by(() => {
    const list = cards;
    if (list === null) return [];
    return sortCards(
      list.filter((c) => matchesSearch(c, query) && matchesFilter(c, filter)),
      sort,
    );
  });

  const statusPill: Record<
    ProjectCardViewModel["status"],
    { label: string; class: string }
  > = {
    draft: { label: "Draft", class: "bg-muted text-muted-foreground" },
    needs_action: { label: "Needs you", class: "bg-primary text-primary-foreground" },
    with_approver: { label: "With approver", class: "bg-muted text-muted-foreground" },
    complete: { label: "Complete", class: "bg-[#1f7a4d] text-white" },
    in_progress: { label: "In progress", class: "bg-muted text-muted-foreground" },
  };

  const cellColor: Record<ProjectCardViewModel["cells"][number], string> = {
    complied: "bg-primary",
    submitted: "bg-[var(--color-accent-300)]",
    returned: "bg-destructive",
    not_started: "bg-[#e2e3ee]",
  };

  function clearFilters() {
    query = "";
    filter = "All";
  }
</script>

<main class="mx-auto max-w-6xl space-y-6 p-8">
  <header class="flex items-end justify-between gap-6">
    <div>
      <div class="text-[10px] tracking-widest text-primary uppercase">My projects</div>
      <h1 class="mt-1 text-4xl">Good morning, Kim</h1>
      <p class="mt-1.5 text-sm text-muted-foreground">
        {#if stats}
          {stats[0].value} record{stats[0].value === 1 ? "" : "s"} you manage. {stats[1].value} submission{stats[1]
            .value === 1
            ? ""
            : "s"} are with approvers, and {stats[2].value} todo{stats[2].value === 1 ? "" : "s"} need rework.
        {:else}
          Loading your records…
        {/if}
      </p>
    </div>
    <Button onclick={() => navigate("/wizard")}>Create project</Button>
  </header>

  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  {#if stats}
    <div class="rounded-2xl border border-border bg-card shadow-sm">
      <div class="px-5 pt-3.5 text-[10px] tracking-widest text-muted-foreground uppercase">Overview · this week</div>
      <div class="grid grid-cols-4 px-2.5 pb-1.5">
        {#each stats as s (s.label)}
          <div class="border-r border-border px-3 py-3 pb-4 last:border-r-0">
            <div class="text-[10px] tracking-wide text-muted-foreground uppercase">{s.label}</div>
            <div class="mt-1.5 font-heading text-[30px] leading-none font-medium" class:text-destructive={s.hot}>
              {s.value}
            </div>
            <div class="text-[11.5px] text-muted-foreground">{s.note}</div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if cards === null}
    <p class="text-sm text-muted-foreground">Loading projects…</p>
  {:else if cards.length === 0}
    <div class="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card py-14 text-center shadow-sm">
      <p class="text-sm text-muted-foreground">No projects yet.</p>
      <Button onclick={() => navigate("/wizard")}>Create your first project</Button>
    </div>
  {:else}
    <div>
      <div class="mb-1.5 flex items-center gap-3">
        <h2 class="text-2xl">My project records</h2>
        {#if stats && stats[1].value > 0}
          <span
            class="inline-flex h-6 items-center gap-1 rounded-full bg-primary px-2.5 text-xs text-primary-foreground"
          >
            {stats[1].value} out for approval
          </span>
        {/if}
      </div>
      <p class="text-[12.5px] text-muted-foreground">
        Cells show todo progress. Anything with an approver or returned for rework is flagged on the record.
      </p>

      <div class="mt-4 flex flex-wrap items-center gap-3">
        <input
          class="max-w-72 rounded-lg border border-input bg-background px-3.5 py-2.5 text-sm"
          bind:value={query}
          placeholder="Search name or code"
        />
        <div class="flex overflow-hidden rounded-lg border border-border">
          {#each filterCounts ?? [] as f, i (f.key)}
            <button
              type="button"
              onclick={() => (filter = f.key)}
              class={[
                "flex items-center gap-1.5 px-3.5 py-2 font-heading text-xs font-medium whitespace-nowrap transition-colors",
                i > 0 && "border-l border-border",
                filter === f.key ? "bg-primary text-primary-foreground" : "bg-background hover:bg-muted",
              ]}
            >
              <span>{f.key}</span>
              <span class="opacity-55">{f.count}</span>
            </button>
          {/each}
        </div>
        <div class="ml-auto flex items-center gap-2">
          <span class="text-[10px] tracking-wide text-muted-foreground uppercase">Sort</span>
          <select
            class="w-48 rounded-lg border border-input bg-background px-3 py-2 text-sm"
            bind:value={sort}
          >
            {#each SORT_OPTIONS as opt (opt.id)}
              <option value={opt.id}>{opt.label}</option>
            {/each}
          </select>
        </div>
      </div>

      <div class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {#each shownCards as card (card.id)}
          {@const pill = statusPill[card.status]}
          <div class="relative">
            <button
              type="button"
              onclick={() => goToProject(card.id)}
              class="flex min-h-[214px] w-full flex-col gap-2.5 rounded-2xl border border-border bg-card p-6 pr-14 text-left shadow-sm transition hover:border-foreground/40 hover:shadow-md"
            >
              <div class="flex items-baseline gap-2">
                <span class="text-[10px] tracking-wide text-primary uppercase">{card.code}</span>
                <span
                  class="ml-auto inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-heading text-[11px] font-medium tracking-wide whitespace-nowrap uppercase {pill.class}"
                >
                  {pill.label}
                </span>
              </div>
              <div class="font-heading text-xl leading-tight font-medium">{card.name}</div>

              {#if card.alert}
                <div
                  class="flex items-start gap-2.5 rounded-xl border-l-4 border-destructive bg-destructive/10 px-3 py-2.5"
                >
                  <div class="min-w-0 flex-1">
                    <div class="text-[9.5px] tracking-wide text-destructive uppercase">
                      {card.alert.kind === "returned" ? "Needs rework" : "Awaiting approval"} · {card.alert
                        .waitingLabel}
                    </div>
                    <div class="mt-0.5 font-heading text-xs font-medium text-destructive">{card.alert.title}</div>
                    <div class="text-[11px] text-destructive/80">{card.alert.authority}</div>
                  </div>
                </div>
              {/if}

              {#if card.isDraft}
                <div class="mt-auto flex items-center gap-2.5 border-t border-border pt-3">
                  <span class="text-[11.5px] text-muted-foreground">Classification not started</span>
                  <span class="ml-auto font-heading text-[11.5px] font-medium tracking-wide text-primary uppercase"
                    >Resume setup →</span
                  >
                </div>
              {:else}
                <div class="mt-auto w-full">
                  <div class="flex gap-0.5">
                    {#each card.cells as cell, i (i)}
                      <span class="h-4 flex-1 {cellColor[cell]}"></span>
                    {:else}
                      <span class="h-4 flex-1 bg-[#e2e3ee]"></span>
                    {/each}
                  </div>
                  <div class="mt-1.5 flex justify-between text-[11px] text-muted-foreground">
                    <span>{card.stepLabel}</span>
                    <span>{card.pct}%</span>
                  </div>
                </div>
              {/if}
            </button>
            <button
              type="button"
              title={isProjectFavorited(card.id) ? "Remove from favourites" : "Add to favourites"}
              onclick={(e) => {
                e.stopPropagation();
                toggleFavoriteProject(card.id);
              }}
              class="absolute top-5 right-5 flex size-7 items-center justify-center rounded-lg transition-colors hover:bg-foreground/5"
              class:text-primary={isProjectFavorited(card.id)}
              class:text-muted-foreground={!isProjectFavorited(card.id)}
            >
              <StarIcon class="size-4" fill={isProjectFavorited(card.id) ? "currentColor" : "none"} />
            </button>
          </div>
        {/each}
      </div>

      {#if shownCards.length === 0}
        <div class="flex items-center gap-4 border-t border-border py-8">
          <span class="text-sm text-muted-foreground">No records match this search and filter.</span>
          <Button variant="secondary" onclick={clearFilters}>Clear filters</Button>
        </div>
      {/if}
    </div>
  {/if}
</main>

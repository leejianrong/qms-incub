<script lang="ts">
  // V18 step 5/6: the real /favourites page, replacing Console.svelte's
  // stub. Lists favourited projects and favourited blog posts side by
  // side, per ui-reference/'s isFavs branch (which only covers articles —
  // adapted here to also cover projects since consoleState.svelte.ts
  // already tracks that favourite set, unused until this slice). Row
  // rendering reuses projectCards.ts's buildProjectCard for projects and
  // blogCards.ts's deriveExcerpt/formatPublishedAt for posts, so both
  // stay consistent with the dashboard and Blog views rather than
  // reinventing their view-models here.
  import StarIcon from "@lucide/svelte/icons/star";
  import { Button } from "$lib/components/ui/button/index.js";
  import { resolveApiBase, listProjects, listProcessSteps, listBlogPosts, getProject, type Project, type TodoItem, type BlogPost } from "$lib/api";
  import { buildProjectCard, type ProjectCardViewModel } from "$lib/projectCards";
  import { deriveExcerpt, favoritedPosts, formatPublishedAt, publishedPosts, sortByRecency } from "$lib/blogCards";
  import {
    goToProject,
    getFavoriteProjectIds,
    toggleFavoriteProject,
    getFavoritePostIds,
    toggleFavoritePost,
  } from "$lib/consoleState.svelte";
  import { navigate } from "$lib/router.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  let cards = $state<ProjectCardViewModel[] | null>(null);
  let posts = $state<BlogPost[] | null>(null);
  let error = $state<string | null>(null);

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
      cards = details.map((d) => buildProjectCard(d.project, d.todos, steps));
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
    try {
      posts = await listBlogPosts(apiBase);
    } catch {
      posts = [];
    }
  }

  load();

  const favoriteProjectCards = $derived.by(() => {
    if (cards === null) return null;
    const ids = getFavoriteProjectIds();
    return cards.filter((c) => !!ids[c.id]);
  });

  const favoritePosts = $derived.by(() => {
    if (posts === null) return null;
    return sortByRecency(favoritedPosts(publishedPosts(posts), getFavoritePostIds()));
  });

  const loaded = $derived(favoriteProjectCards !== null && favoritePosts !== null);
  const isEmpty = $derived(loaded && (favoriteProjectCards?.length ?? 0) === 0 && (favoritePosts?.length ?? 0) === 0);
</script>

<main class="mx-auto max-w-6xl space-y-8 p-8">
  <header class="border-b border-border pb-6">
    <div class="text-[10px] tracking-widest text-primary uppercase">Saved</div>
    <h1 class="mt-1 text-4xl">Favourites</h1>
    <p class="mt-1.5 text-sm text-muted-foreground">
      Projects and posts you starred. Star anything from the dashboard or the Blog to keep it here.
    </p>
  </header>

  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  {#if !loaded}
    <p class="text-sm text-muted-foreground">Loading favourites…</p>
  {:else if isEmpty}
    <div class="rounded-2xl border border-dashed border-border p-11 text-center text-sm text-muted-foreground">
      Nothing favourited yet. Tap the star on a project or a Blog post and it will appear here.
    </div>
  {:else}
    {#if favoriteProjectCards && favoriteProjectCards.length > 0}
      <section>
        <div class="mb-2 flex items-baseline gap-2.5">
          <h2 class="text-2xl">Projects</h2>
          <span class="text-xs text-muted-foreground">
            {favoriteProjectCards.length} {favoriteProjectCards.length === 1 ? "record" : "records"}
          </span>
        </div>
        <div class="flex flex-col border-t border-border">
          {#each favoriteProjectCards as card (card.id)}
            <div class="flex items-center gap-4 border-b border-border py-4">
              <button
                type="button"
                onclick={() => goToProject(card.id)}
                class="flex min-w-0 flex-1 items-baseline gap-3 text-left"
              >
                <span class="text-[10px] tracking-wide text-primary uppercase">{card.code}</span>
                <span class="min-w-0 truncate font-heading text-base font-medium">{card.name}</span>
                <span class="ml-auto text-xs text-muted-foreground">{card.pct}% complete</span>
              </button>
              <button
                type="button"
                title="Remove from favourites"
                onclick={() => toggleFavoriteProject(card.id)}
                class="flex size-8 flex-none items-center justify-center rounded-lg text-primary transition-colors hover:bg-foreground/5"
              >
                <StarIcon class="size-4" fill="currentColor" />
              </button>
            </div>
          {/each}
        </div>
      </section>
    {/if}

    {#if favoritePosts && favoritePosts.length > 0}
      <section>
        <div class="mb-2 flex items-baseline gap-2.5">
          <h2 class="text-2xl">Articles</h2>
          <span class="text-xs text-muted-foreground">
            {favoritePosts.length} {favoritePosts.length === 1 ? "article" : "articles"}
          </span>
        </div>
        <div class="flex flex-col border-t border-border">
          {#each favoritePosts as post (post.id)}
            <div class="flex items-start gap-4 border-b border-border py-4">
              <button
                type="button"
                title="Remove from favourites"
                onclick={() => toggleFavoritePost(post.id)}
                class="flex size-8 flex-none items-center justify-center rounded-lg text-primary transition-colors hover:bg-foreground/5"
              >
                <StarIcon class="size-4" fill="currentColor" />
              </button>
              <button
                type="button"
                onclick={() => navigate(`/blog?id=${post.id}`)}
                class="min-w-0 flex-1 text-left"
              >
                <span class="block text-[10px] tracking-wide text-primary uppercase">
                  {formatPublishedAt(post.published_at)}
                </span>
                <span class="mt-1 block font-heading text-lg leading-tight font-medium">{post.title}</span>
                <span class="mt-1 block text-[13px] leading-relaxed text-muted-foreground">
                  {deriveExcerpt(post.body)}
                </span>
              </button>
            </div>
          {/each}
        </div>
      </section>
    {/if}
  {/if}

  {#if loaded && isEmpty}
    <div class="flex justify-center">
      <Button onclick={() => navigate("/blog")}>Browse the blog</Button>
    </div>
  {/if}
</main>

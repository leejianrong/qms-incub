<script lang="ts">
  // V18 step 5: the PM-facing Blog list/detail view, replacing the stub
  // Console.svelte used to render for the "blog" route. Consumes V6's
  // existing listBlogPosts/getBlogPost endpoints — no new backend work.
  // Layout follows ui-reference/QMS Console.dc.html's isBlog branch (hero +
  // grid + detail-with-comments-sidebar), adapted to our real BlogPost
  // shape (title/body/published_at only — see blogCards.ts for why the
  // reference's author/kicker/read-time/pull-quote fields are skipped
  // rather than invented). Search/excerpt/paragraph/date logic lives in
  // blogCards.ts so it's unit-tested without rendering; comments are
  // client-only state in blogComments.svelte.ts (Q53, same pattern as
  // ProjectDetail.svelte's Discussion thread).
  import { Button } from "$lib/components/ui/button/index.js";
  import StarIcon from "@lucide/svelte/icons/star";
  import SearchIcon from "@lucide/svelte/icons/search";
  import ArrowLeftIcon from "@lucide/svelte/icons/arrow-left";
  import MessageSquareIcon from "@lucide/svelte/icons/message-square";
  import { resolveApiBase, listBlogPosts, type BlogPost } from "$lib/api";
  import {
    deriveExcerpt,
    formatPublishedAt,
    matchesBlogSearch,
    paragraphsOf,
    publishedPosts,
    sortByRecency,
  } from "$lib/blogCards";
  import { isPostFavorited, toggleFavoritePost } from "$lib/consoleState.svelte";
  import { getComments, postComment } from "$lib/blogComments.svelte";
  import { navigate, routeParam } from "$lib/router.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  let posts = $state<BlogPost[] | null>(null);
  let error = $state<string | null>(null);
  let query = $state("");
  let commentDraft = $state("");

  async function load() {
    error = null;
    try {
      posts = await listBlogPosts(apiBase);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }

  load();

  const postId = $derived(routeParam("id"));

  const visiblePosts = $derived.by(() => (posts === null ? [] : sortByRecency(publishedPosts(posts))));

  const selectedPost = $derived(postId ? (visiblePosts.find((p) => p.id === postId) ?? null) : null);

  const searching = $derived(query.trim().length > 0);

  const filteredPosts = $derived(visiblePosts.filter((p) => matchesBlogSearch(p, query)));

  const heroPost = $derived(!searching && visiblePosts.length > 0 ? visiblePosts[0] : null);

  const restPosts = $derived(searching ? filteredPosts : filteredPosts.filter((p) => p.id !== heroPost?.id));

  function openPost(id: string) {
    navigate(`/blog?id=${id}`);
  }

  function backToAll() {
    commentDraft = "";
    navigate("/blog");
  }

  const comments = $derived(selectedPost ? getComments(selectedPost.id) : []);

  function submitComment() {
    if (!selectedPost || !commentDraft.trim()) return;
    postComment(selectedPost.id, "Kim Alvarez", "Project manager", commentDraft);
    commentDraft = "";
  }
</script>

<main class="mx-auto max-w-6xl space-y-6 p-8">
  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  {#if posts === null}
    {#if !error}
      <p class="text-sm text-muted-foreground">Loading posts…</p>
    {/if}
  {:else if selectedPost}
    <!-- Detail view -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      <article class="min-w-0 space-y-4">
        <div class="flex items-center gap-3">
          <Button variant="ghost" size="sm" onclick={backToAll}>
            <ArrowLeftIcon class="size-4" /> All posts
          </Button>
          <button
            type="button"
            title={isPostFavorited(selectedPost.id) ? "Remove from favourites" : "Add to favourites"}
            onclick={() => toggleFavoritePost(selectedPost.id)}
            class={[
              "flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs transition-colors hover:border-primary",
              isPostFavorited(selectedPost.id) ? "text-primary" : "text-muted-foreground",
            ]}
          >
            <StarIcon class="size-3.5" fill={isPostFavorited(selectedPost.id) ? "currentColor" : "none"} />
            {isPostFavorited(selectedPost.id) ? "Favourited" : "Favourite"}
          </button>
        </div>

        <div>
          <div class="text-[11px] tracking-wide text-primary uppercase">{formatPublishedAt(selectedPost.published_at)}</div>
          <h1 class="mt-1 max-w-[20ch] text-[34px] leading-tight font-medium">{selectedPost.title}</h1>
        </div>
        <hr class="border-border" />
        {#each paragraphsOf(selectedPost.body) as para, i (i)}
          <p class="max-w-[70ch] text-base leading-relaxed">{para}</p>
        {:else}
          <p class="text-sm text-muted-foreground">This post has no body text.</p>
        {/each}
      </article>

      <aside class="rounded-2xl border border-border bg-card p-5 shadow-sm lg:sticky lg:top-20 lg:self-start">
        <div class="flex items-center gap-2.5">
          <span class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-accent text-primary">
            <MessageSquareIcon class="size-[18px]" />
          </span>
          <span class="font-heading text-base font-medium">Comments</span>
          <span class="text-xs text-muted-foreground">{comments.length}</span>
        </div>
        <p class="mt-1.5 text-[11.5px] text-muted-foreground">
          Visible to everyone on the QMS platform — non-persistent for now, clears on reload.
        </p>
        <div class="mt-3 space-y-1">
          {#each comments as comment (comment.postedAt)}
            <div class="border-t border-border py-3 first:border-t-0 first:pt-0">
              <div class="flex items-baseline gap-2">
                <span class="font-heading text-[13px] font-medium">{comment.who}</span>
                <span class="text-[11px] text-muted-foreground">{comment.role}</span>
              </div>
              <p class="mt-1.5 text-[13.5px] leading-relaxed">{comment.text}</p>
            </div>
          {:else}
            <p class="py-3 text-[12.5px] text-muted-foreground">No comments yet. Be the first to add one.</p>
          {/each}
        </div>
        <form
          class="mt-3 space-y-2"
          onsubmit={(event) => {
            event.preventDefault();
            submitComment();
          }}
        >
          <textarea
            class="min-h-[88px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
            bind:value={commentDraft}
            placeholder="Add a comment…"
          ></textarea>
          <Button type="submit" class="w-full" disabled={!commentDraft.trim()}>Post comment</Button>
        </form>
      </aside>
    </div>
  {:else}
    <!-- List view -->
    <header class="space-y-4 border-b border-border pb-6">
      <div>
        <div class="text-[10px] tracking-widest text-primary uppercase">Blog</div>
        <h1 class="mt-1 text-4xl">Blog</h1>
        <p class="mt-1.5 text-sm text-muted-foreground">
          What teams are learning and what changed in the QMS.
        </p>
      </div>
      <div class="relative max-w-md">
        <SearchIcon class="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          class="w-full rounded-lg border border-input bg-background py-2.5 pr-3.5 pl-9 text-sm"
          bind:value={query}
          placeholder="Search posts"
        />
      </div>
    </header>

    {#if visiblePosts.length === 0}
      <div class="flex flex-col items-center gap-2 rounded-2xl border border-border bg-card py-14 text-center shadow-sm">
        <p class="text-sm text-muted-foreground">No posts have been published yet.</p>
      </div>
    {:else}
      {#if heroPost}
        <button
          type="button"
          onclick={() => openPost(heroPost.id)}
          class="grid w-full grid-cols-1 overflow-hidden rounded-2xl border border-border bg-card text-left shadow-sm transition hover:border-foreground/40 hover:shadow-md md:grid-cols-[1.4fr_1fr]"
        >
          <div class="space-y-3 p-8">
            <div class="flex items-center gap-2.5">
              <span class="rounded-md bg-primary px-2 py-0.5 text-[10px] font-medium tracking-wide text-primary-foreground uppercase">
                Latest
              </span>
              <span class="text-[11px] text-muted-foreground">{formatPublishedAt(heroPost.published_at)}</span>
            </div>
            <div class="max-w-[22ch] font-heading text-[38px] leading-[1.05] font-medium">{heroPost.title}</div>
            <p class="max-w-[56ch] text-[15px] leading-relaxed text-muted-foreground">{deriveExcerpt(heroPost.body, 220)}</p>
            <div class="flex items-center gap-2 border-t border-border pt-3 text-xs text-muted-foreground">
              <span>{formatPublishedAt(heroPost.published_at)}</span>
              <span class="ml-auto font-heading text-[13px] font-medium text-primary">Read →</span>
            </div>
          </div>
          <div class="flex flex-col justify-between bg-primary p-8 text-primary-foreground">
            <div class="text-[10px] tracking-widest uppercase opacity-80">QMS Rev. 4.2</div>
            <div class="text-2xl leading-tight font-medium">{deriveExcerpt(heroPost.body, 100)}</div>
          </div>
        </button>
      {/if}

      <div class="flex items-baseline gap-2.5 pt-2">
        <h2 class="text-2xl">{searching ? "Search results" : "Earlier posts"}</h2>
        <span class="text-xs text-muted-foreground">
          {restPosts.length} {restPosts.length === 1 ? "post" : "posts"}
        </span>
        {#if searching}
          <button type="button" class="ml-auto text-xs text-primary hover:underline" onclick={() => (query = "")}>
            Clear search
          </button>
        {/if}
      </div>

      {#if restPosts.length === 0}
        <div class="rounded-2xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
          Nothing matches that search. Try a different word, or clear it.
        </div>
      {:else}
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {#each restPosts as post (post.id)}
            <div class="relative">
              <button
                type="button"
                onclick={() => openPost(post.id)}
                class="flex h-full w-full flex-col gap-2.5 rounded-2xl border border-border bg-card p-5 pr-12 text-left shadow-sm transition hover:border-foreground/40 hover:shadow-md"
              >
                <span class="text-[11px] text-muted-foreground">{formatPublishedAt(post.published_at)}</span>
                <span class="font-heading text-lg leading-tight font-medium">{post.title}</span>
                <span class="text-[13px] leading-relaxed text-muted-foreground">{deriveExcerpt(post.body)}</span>
                <span class="mt-auto pt-2 text-xs font-medium text-primary">Read →</span>
              </button>
              <button
                type="button"
                title={isPostFavorited(post.id) ? "Remove from favourites" : "Add to favourites"}
                onclick={(e) => {
                  e.stopPropagation();
                  toggleFavoritePost(post.id);
                }}
                class="absolute top-4 right-4 flex size-7 items-center justify-center rounded-lg transition-colors hover:bg-foreground/5"
                class:text-primary={isPostFavorited(post.id)}
                class:text-muted-foreground={!isPostFavorited(post.id)}
              >
                <StarIcon class="size-4" fill={isPostFavorited(post.id) ? "currentColor" : "none"} />
              </button>
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  {/if}
</main>

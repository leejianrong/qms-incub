<script lang="ts">
  // V13: the console shell for the core PM workflow. main.ts mounts this
  // component for "/", "/wizard" and "/project" — it owns picking which of
  // those three views to render (via lib/router.svelte.ts) and wraps them
  // all in the same persistent Shell (header/nav), so moving between the
  // dashboard, the create-project wizard and a project's detail view never
  // re-mounts the whole app.
  import Shell from "./Shell.svelte";
  import ProjectsDashboard from "./ProjectsDashboard.svelte";
  import Wizard from "./Wizard.svelte";
  import ProjectDetail from "./ProjectDetail.svelte";
  import { routePath } from "$lib/router.svelte";

  const view = $derived(
    routePath() === "/wizard"
      ? "wizard"
      : routePath() === "/project"
        ? "project"
        : routePath() === "/blog"
          ? "blog"
          : routePath() === "/faq"
            ? "faq"
            : routePath() === "/favourites"
              ? "favourites"
              : "dashboard",
  );
</script>

<Shell>
  {#if view === "wizard"}
    <Wizard />
  {:else if view === "project"}
    <ProjectDetail />
  {:else if view === "blog" || view === "faq" || view === "favourites"}
    <!-- V18 build plan steps 5/6 land the real Blog/FAQ reader and
         favourites list; the Shell slice only needs these routes to
         exist so the header's nav/favourites are clickable. -->
    <main class="mx-auto max-w-3xl p-8">
      <p class="text-sm text-muted-foreground">
        {#if view === "blog"}
          The Blog reader lands in a follow-up slice (V18 step 5).
        {:else if view === "faq"}
          The FAQ view lands in a follow-up slice (V18 step 6).
        {:else}
          Nothing favourited yet — favouriting projects and posts lands alongside their
          respective slices (V18 steps 2 and 5).
        {/if}
      </p>
    </main>
  {:else}
    <ProjectsDashboard />
  {/if}
</Shell>

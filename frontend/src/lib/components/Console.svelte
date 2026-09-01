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
  import Blog from "./Blog.svelte";
  import Favourites from "./Favourites.svelte";
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
  {:else if view === "blog"}
    <Blog />
  {:else if view === "favourites"}
    <Favourites />
  {:else if view === "faq"}
    <!-- V18 step 6 lands the real FAQ reader; the Shell slice only needs
         this route to exist so the header's nav is clickable. -->
    <main class="mx-auto max-w-3xl p-8">
      <p class="text-sm text-muted-foreground">The FAQ view lands in a follow-up slice (V18 step 6).</p>
    </main>
  {:else}
    <ProjectsDashboard />
  {/if}
</Shell>

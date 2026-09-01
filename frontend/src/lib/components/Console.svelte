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
    routePath() === "/wizard" ? "wizard" : routePath() === "/project" ? "project" : "dashboard",
  );
</script>

<Shell>
  {#if view === "wizard"}
    <Wizard />
  {:else if view === "project"}
    <ProjectDetail />
  {:else}
    <ProjectsDashboard />
  {/if}
</Shell>

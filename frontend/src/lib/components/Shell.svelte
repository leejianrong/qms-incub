<script lang="ts">
  import type { Snippet } from "svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import { navigate, routePath } from "$lib/router.svelte";

  let { children }: { children?: Snippet } = $props();

  function go(path: string, event: MouseEvent) {
    event.preventDefault();
    navigate(path);
  }
</script>

<div class="min-h-screen bg-background text-foreground">
  <header class="border-b border-border bg-card">
    <div class="mx-auto flex max-w-6xl items-center gap-6 px-8 py-4">
      <a href="/" onclick={(event) => go("/", event)} class="text-lg font-semibold tracking-tight">
        QMS Console
      </a>
      <nav class="flex items-center gap-4 text-sm">
        <a
          href="/"
          onclick={(event) => go("/", event)}
          class="text-muted-foreground hover:text-foreground"
          class:text-foreground={routePath() === "/"}
          class:font-medium={routePath() === "/"}
        >
          Projects
        </a>
      </nav>
      <Button size="sm" class="ml-auto" onclick={() => navigate("/wizard")}>Create project</Button>
    </div>
  </header>

  <div>
    {@render children?.()}
  </div>
</div>

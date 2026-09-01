<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { resolveApiBase, getProject, type ProjectWithTodos } from "$lib/api";

  const apiBase = resolveApiBase(import.meta.env);
  const projectId = new URLSearchParams(window.location.search).get("id") ?? "";

  let data = $state<ProjectWithTodos | null>(null);
  let error = $state<string | null>(null);

  getProject(apiBase, projectId)
    .then((result) => (data = result))
    .catch((err) => (error = err instanceof Error ? err.message : String(err)));

  const tierVariant: Record<string, "outline" | "secondary" | "destructive"> = {
    low: "outline",
    medium: "secondary",
    high: "destructive",
  };
</script>

<main class="mx-auto max-w-3xl space-y-6 p-8">
  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {:else if !data}
    <p class="text-sm text-muted-foreground">Loading project…</p>
  {:else}
    <header class="flex items-center gap-3">
      <h1 class="text-2xl font-medium">{data.project.name}</h1>
      <Badge variant={tierVariant[data.project.risk_tier] ?? "outline"}>
        {data.project.risk_tier} tier
      </Badge>
    </header>

    <Card.Root>
      <Card.Header>
        <Card.Title>Compliance todo list</Card.Title>
        <Card.Description>{data.todos.length} item(s) generated from this risk tier</Card.Description>
      </Card.Header>
      <Card.Content>
        {#if data.todos.length === 0}
          <p class="text-sm text-muted-foreground">
            No Requirements are tagged for this risk tier yet.
          </p>
        {:else}
          <ul class="space-y-3">
            {#each data.todos as todo (todo.id)}
              <li class="rounded-md border border-border p-3">
                <div class="flex items-center justify-between gap-2">
                  <p class="text-sm font-medium">{todo.requirement_description}</p>
                  <Badge variant={todo.status === "complied" ? "secondary" : "outline"}>
                    {todo.status === "complied" ? "Complied" : "Pending"}
                  </Badge>
                </div>
                <p class="text-xs text-muted-foreground">
                  {todo.standard_name} &gt; {todo.clause_text}
                </p>
              </li>
            {/each}
          </ul>
        {/if}
      </Card.Content>
    </Card.Root>
  {/if}
</main>

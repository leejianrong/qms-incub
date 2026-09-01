<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import {
    resolveApiBase,
    listProjects,
    getProject,
    type Project,
    type ProjectWithTodos,
  } from "$lib/api";
  import { navigate } from "$lib/router.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  interface ProjectSummary {
    project: Project;
    compliancePercentage: number | null;
    todoCount: number;
  }

  let summaries = $state<ProjectSummary[] | null>(null);
  let error = $state<string | null>(null);

  async function summarize(project: Project): Promise<ProjectSummary> {
    if (project.risk_tier === null) {
      // Not classified yet — there's no generated todo list to summarize.
      return { project, compliancePercentage: null, todoCount: 0 };
    }
    try {
      const detail: ProjectWithTodos = await getProject(apiBase, project.id);
      return {
        project,
        compliancePercentage: detail.compliance_percentage,
        todoCount: detail.todos.length,
      };
    } catch {
      return { project, compliancePercentage: null, todoCount: 0 };
    }
  }

  async function load() {
    error = null;
    try {
      const projects = await listProjects(apiBase);
      summaries = await Promise.all(projects.map(summarize));
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }

  load();

  const tierVariant: Record<string, "outline" | "secondary" | "destructive"> = {
    low: "outline",
    medium: "secondary",
    high: "destructive",
  };

  function open(project: Project) {
    navigate(`/project?id=${project.id}`);
  }
</script>

<main class="mx-auto max-w-5xl space-y-6 p-8">
  <header class="flex items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-medium">Projects</h1>
      <p class="text-sm text-muted-foreground">
        Every project you manage, its risk tier, and how far its compliance plan has progressed.
      </p>
    </div>
    <Button onclick={() => navigate("/wizard")}>Create project</Button>
  </header>

  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  {#if summaries === null}
    <p class="text-sm text-muted-foreground">Loading projects…</p>
  {:else if summaries.length === 0}
    <Card.Root>
      <Card.Content class="flex flex-col items-center gap-3 py-14 text-center">
        <p class="text-sm text-muted-foreground">No projects yet.</p>
        <Button onclick={() => navigate("/wizard")}>Create your first project</Button>
      </Card.Content>
    </Card.Root>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each summaries as summary (summary.project.id)}
        <button type="button" class="text-left" onclick={() => open(summary.project)}>
          <Card.Root class="h-full transition hover:border-foreground/40 hover:shadow-md">
            <Card.Header>
              <Card.Title>{summary.project.name}</Card.Title>
              <Card.Description>
                {#if summary.project.risk_tier}
                  {summary.todoCount} compliance todo{summary.todoCount === 1 ? "" : "s"}
                {:else}
                  Not yet classified
                {/if}
              </Card.Description>
            </Card.Header>
            <Card.Content class="flex flex-wrap items-center gap-2">
              <Badge variant={tierVariant[summary.project.risk_tier ?? ""] ?? "outline"}>
                {summary.project.risk_tier ?? "unclassified"}{summary.project.risk_tier ? " tier" : ""}
              </Badge>
              {#if summary.compliancePercentage !== null}
                <Badge variant="outline">{Math.round(summary.compliancePercentage)}% complied</Badge>
              {/if}
            </Card.Content>
          </Card.Root>
        </button>
      {/each}
    </div>
  {/if}
</main>

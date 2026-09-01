<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import {
    askChat,
    resolveApiBase,
    getProject,
    uploadArtifact,
    listProcessSteps,
    type ProjectWithTodos,
    type ProcessStep,
    type TodoItem,
    type ChatAnswer,
  } from "$lib/api";
  import { approvalRouteViewModel } from "$lib/approvalRoute";

  const apiBase = resolveApiBase(import.meta.env);
  const projectId = new URLSearchParams(window.location.search).get("id") ?? "";

  let data = $state<ProjectWithTodos | null>(null);
  let steps = $state<ProcessStep[]>([]);
  let error = $state<string | null>(null);
  let uploadingTodoId = $state<string | null>(null);
  let selectedTodoId = $state<string | null>(null);
  let navigatorCollapsed = $state(false);
  let expandedStepId = $state<string | null>(null);
  let question = $state("");
  let asking = $state(false);
  let chatResult = $state<ChatAnswer | null>(null);
  let chatError = $state<string | null>(null);

  function load() {
    Promise.all([getProject(apiBase, projectId), listProcessSteps(apiBase)])
      .then(([project, processSteps]) => {
        data = project;
        steps = processSteps;
        if (expandedStepId === null && processSteps.length > 0) {
          expandedStepId = processSteps[0].id;
        }
      })
      .catch((err) => (error = err instanceof Error ? err.message : String(err)));
  }

  load();

  async function attest(todoId: string, files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    uploadingTodoId = todoId;
    error = null;
    try {
      await uploadArtifact(apiBase, todoId, file);
      load();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      uploadingTodoId = null;
    }
  }

  async function ask() {
    if (!question.trim() || asking || !projectId) return;
    asking = true;
    chatError = null;
    try {
      chatResult = await askChat(apiBase, question, projectId);
    } catch (err) {
      chatError = err instanceof Error ? err.message : String(err);
    } finally {
      asking = false;
    }
  }

  const tierVariant: Record<string, "outline" | "secondary" | "destructive"> = {
    low: "outline",
    medium: "secondary",
    high: "destructive",
  };

  function todosForStep(stepId: string): TodoItem[] {
    return data?.todos.filter((t) => t.process_step_id === stepId) ?? [];
  }

  function stepProgress(stepId: string): { done: number; total: number } {
    const todos = todosForStep(stepId);
    return { done: todos.filter((t) => t.status === "complied").length, total: todos.length };
  }

  const selectedTodo = $derived(data?.todos.find((t) => t.id === selectedTodoId) ?? null);

  function selectTodo(todo: TodoItem) {
    selectedTodoId = todo.id;
    expandedStepId = todo.process_step_id;
  }
</script>

<main class="mx-auto max-w-6xl space-y-6 p-8">
  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  {#if !data}
    <p class="text-sm text-muted-foreground">Loading project…</p>
  {:else}
    <header class="flex items-center gap-3">
      <h1 class="text-2xl font-medium">{data.project.name}</h1>
      <Badge variant={tierVariant[data.project.risk_tier ?? ""] ?? "outline"}>
        {data.project.risk_tier ?? "unclassified"}{data.project.risk_tier ? " tier" : ""}
      </Badge>
      <Badge variant="outline">{Math.round(data.compliance_percentage)}% complied</Badge>
    </header>

    <div class="flex gap-6">
      <!-- Left: collapsible plan navigator -->
      <nav
        class="shrink-0 rounded-md border border-border bg-card transition-all"
        class:w-14={navigatorCollapsed}
        class:w-72={!navigatorCollapsed}
        aria-label="Plan navigator"
      >
        <div class="flex items-center justify-between border-b border-border p-2">
          {#if !navigatorCollapsed}
            <span class="px-1 text-xs font-medium text-muted-foreground">Plan navigator</span>
          {/if}
          <Button
            size="sm"
            variant="ghost"
            aria-label={navigatorCollapsed ? "Expand navigator" : "Collapse navigator"}
            onclick={() => (navigatorCollapsed = !navigatorCollapsed)}
          >
            {navigatorCollapsed ? "»" : "«"}
          </Button>
        </div>

        <ul class="space-y-1 p-2">
          {#each steps as step (step.id)}
            {@const progress = stepProgress(step.id)}
            {@const pct = progress.total === 0 ? 0 : Math.round((progress.done / progress.total) * 100)}
            <li>
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-md p-2 text-left text-sm hover:bg-accent"
                title={step.title}
                onclick={() => (expandedStepId = expandedStepId === step.id ? null : step.id)}
              >
                <span
                  class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border text-[10px] font-medium"
                >
                  {step.title.slice(0, 1)}
                </span>
                {#if !navigatorCollapsed}
                  <span class="flex-1 truncate">{step.title}</span>
                  <span class="text-xs text-muted-foreground">{progress.done}/{progress.total}</span>
                {/if}
              </button>

              {#if !navigatorCollapsed}
                <div class="mx-2 h-1 overflow-hidden rounded-full bg-muted">
                  <div class="h-full rounded-full bg-primary" style={`width: ${pct}%`}></div>
                </div>
              {/if}

              {#if !navigatorCollapsed && expandedStepId === step.id}
                <ul class="ml-6 mt-1 space-y-1 border-l border-border pl-2">
                  {#each todosForStep(step.id) as todo (todo.id)}
                    <li>
                      <button
                        type="button"
                        class="block w-full truncate rounded-md p-1.5 text-left text-xs hover:bg-accent"
                        class:bg-accent={selectedTodoId === todo.id}
                        onclick={() => selectTodo(todo)}
                      >
                        {todo.status === "complied" ? "✓ " : ""}{todo.requirement_description}
                      </button>
                    </li>
                  {:else}
                    <li class="p-1.5 text-xs text-muted-foreground">No todos in this step.</li>
                  {/each}
                </ul>
              {/if}
            </li>
          {/each}
        </ul>
      </nav>

      <!-- Right: selected todo detail -->
      <div class="min-w-0 flex-1">
        {#if !selectedTodo}
          <Card.Root>
            <Card.Content class="py-10 text-center text-sm text-muted-foreground">
              Select a todo from the plan navigator to see its details.
            </Card.Content>
          </Card.Root>
        {:else}
          <Card.Root>
            <Card.Header>
              <div class="flex items-center justify-between gap-2">
                <Card.Title>{selectedTodo.requirement_description}</Card.Title>
                <Badge variant={selectedTodo.status === "complied" ? "secondary" : "outline"}>
                  {selectedTodo.status === "complied" ? "Complied" : "Pending"}
                </Badge>
              </div>
              <Card.Description>
                {selectedTodo.standard_name} &gt; {selectedTodo.clause_text}
              </Card.Description>
            </Card.Header>
            <Card.Content>
              {#if selectedTodo.approval_state !== "not_required"}
                {@const route = approvalRouteViewModel(selectedTodo)}
                <div class="mb-3 flex items-center gap-2 text-xs">
                  {#each route.nodes as node, i (node.key)}
                    {#if i > 0}<span class="text-muted-foreground">→</span>{/if}
                    <Badge variant={node.highlighted ? "default" : "outline"}>{node.label}</Badge>
                  {/each}
                </div>
                <p class="mb-3 text-xs text-muted-foreground">
                  {route.statusText} · {route.authority}{route.slaText ? ` · ${route.slaText}` : ""}
                </p>
              {/if}
              {#if selectedTodo.status === "pending"}
                <input
                  type="file"
                  id={`artifact-${selectedTodo.id}`}
                  class="hidden"
                  disabled={uploadingTodoId === selectedTodo.id}
                  onchange={(e) => attest(selectedTodo.id, (e.target as HTMLInputElement).files)}
                />
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={uploadingTodoId === selectedTodo.id}
                  onclick={() => document.getElementById(`artifact-${selectedTodo.id}`)?.click()}
                >
                  {uploadingTodoId === selectedTodo.id ? "Uploading…" : "Upload artifact"}
                </Button>
              {:else}
                <p class="text-sm text-muted-foreground">
                  Self-attested — an artifact has been uploaded against this todo.
                </p>
              {/if}
            </Card.Content>
          </Card.Root>
        {/if}
      </div>
    </div>

    <Card.Root aria-label="Project-aware compliance chat">
      <Card.Header>
        <Card.Title>Ask about this project</Card.Title>
        <Card.Description>
          Answers use this project's current todo and artifact state plus the policy corpus.
        </Card.Description>
      </Card.Header>
      <Card.Content class="space-y-3">
        <form class="flex gap-2" onsubmit={(event) => { event.preventDefault(); ask(); }}>
          <input
            class="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            bind:value={question}
            placeholder="e.g. Am I compliant yet?"
            disabled={asking}
          />
          <Button type="submit" disabled={asking || !question.trim()}>
            {asking ? "Asking…" : "Ask"}
          </Button>
        </form>
        {#if chatError}
          <p class="text-sm text-destructive">Chat error: {chatError}</p>
        {/if}
        {#if chatResult}
          <div class="rounded-md border border-border p-3 text-sm">
            <p>{chatResult.answer}</p>
            {#if chatResult.citations.length > 0}
              <p class="mt-2 text-xs text-muted-foreground">
                Policy sources: {chatResult.citations.map((citation) => citation.document_title).join(", ")}
              </p>
            {/if}
          </div>
        {/if}
      </Card.Content>
    </Card.Root>
  {/if}
</main>

<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import ChevronsLeftIcon from "@lucide/svelte/icons/chevrons-left";
  import ChevronsRightIcon from "@lucide/svelte/icons/chevrons-right";
  import MessageSquareIcon from "@lucide/svelte/icons/message-square";
  import FlagIcon from "@lucide/svelte/icons/flag";
  import PenToolIcon from "@lucide/svelte/icons/pen-tool";
  import HammerIcon from "@lucide/svelte/icons/hammer";
  import FlaskConicalIcon from "@lucide/svelte/icons/flask-conical";
  import RocketIcon from "@lucide/svelte/icons/rocket";
  import CheckCircle2Icon from "@lucide/svelte/icons/check-circle-2";
  import CircleIcon from "@lucide/svelte/icons/circle";
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
  import { projectCode } from "$lib/projectCards";
  import { getComments, postComment } from "$lib/discussionState.svelte";
  import { navigate, routeParam } from "$lib/router.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  // Reactive rather than captured once at mount — the console shell keeps
  // this component mounted while the router changes which project's id is
  // in the URL (e.g. browser back/forward after opening a project from the
  // dashboard), so the id has to track the route, not freeze at first load.
  const projectId = $derived(routeParam("id") ?? "");

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
  let commentDraft = $state("");

  // Refetches this project's data without disturbing the user's current
  // selection — used both for the initial load and to refresh after an
  // artifact upload, where clearing the selected todo would hide the very
  // approval-route update self-attestation just produced.
  function load() {
    if (!projectId) {
      data = null;
      error = "No project selected.";
      return;
    }
    error = null;
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

  $effect(() => {
    // Runs on mount and whenever the route's project id changes (e.g.
    // browser back/forward after opening a different project from the
    // dashboard) — resets the view before loading the new project's data.
    void projectId;
    data = null;
    selectedTodoId = null;
    expandedStepId = null;
    chatResult = null;
    chatError = null;
    load();
  });

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

  function stepNeedsAttention(stepId: string): boolean {
    return todosForStep(stepId).some((t) => t.approval_state === "returned");
  }

  const selectedTodo = $derived(data?.todos.find((t) => t.id === selectedTodoId) ?? null);

  function selectTodo(todo: TodoItem) {
    selectedTodoId = todo.id;
    expandedStepId = todo.process_step_id;
  }

  const STEP_ICONS = [FlagIcon, PenToolIcon, HammerIcon, FlaskConicalIcon, RocketIcon, CheckCircle2Icon];
  function stepIcon(index: number) {
    return STEP_ICONS[index % STEP_ICONS.length] ?? CircleIcon;
  }

  function todoBadge(todo: TodoItem): { label: string; class: string } {
    if (todo.status === "complied") return { label: "Done", class: "text-primary" };
    if (todo.approval_state === "returned") return { label: "Returned", class: "text-destructive" };
    if (todo.approval_state === "submitted") return { label: "In review", class: "text-muted-foreground" };
    return { label: "Open", class: "text-muted-foreground" };
  }

  const comments = $derived(selectedTodo ? getComments(selectedTodo.id) : []);

  function submitComment() {
    if (!selectedTodo || !commentDraft.trim()) return;
    postComment(selectedTodo.id, "Kim Alvarez", "Project manager", commentDraft);
    commentDraft = "";
  }
</script>

<main class="mx-auto max-w-6xl space-y-6 p-8">
  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  {#if !data}
    {#if !error}
      <p class="text-sm text-muted-foreground">Loading project…</p>
    {/if}
  {:else}
    <header class="space-y-4 rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div class="flex items-start gap-5">
        <div class="min-w-0">
          <div class="text-[11px] text-muted-foreground">
            <button type="button" class="hover:text-foreground hover:underline" onclick={() => navigate("/")}>
              Projects
            </button>
            <span> / {projectCode(data.project.id)}</span>
          </div>
          <h1 class="mt-1 text-[32px] leading-tight font-medium">{data.project.name}</h1>
          <div class="mt-2.5 flex flex-wrap gap-2">
            <Badge variant={tierVariant[data.project.risk_tier ?? ""] ?? "outline"}>
              {data.project.risk_tier ?? "unclassified"}{data.project.risk_tier ? " tier" : ""}
            </Badge>
            {#if data.project.aor_extracted_fields}
              <Badge variant="outline">{data.project.aor_extracted_fields.data_classification}</Badge>
            {/if}
          </div>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <div class="h-2.5 flex-1 rounded-full bg-muted">
          <div
            class="h-2.5 rounded-full bg-gradient-to-r from-[var(--color-accent-500)] to-primary"
            style={`width: ${Math.round(data.compliance_percentage)}%`}
          ></div>
        </div>
        <div class="font-heading text-xs font-medium whitespace-nowrap">
          {Math.round(data.compliance_percentage)}% · {data.todos.filter((t) => t.status === "complied").length}/{data
            .todos.length} sub-steps
        </div>
      </div>
    </header>

    <div class="flex gap-5">
      <!-- Left: collapsible plan navigator -->
      <nav
        class="shrink-0 overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all"
        class:w-16={navigatorCollapsed}
        class:w-80={!navigatorCollapsed}
        aria-label="Plan navigator"
      >
        <div class="flex items-center gap-2 border-b border-border p-3">
          {#if !navigatorCollapsed}
            <div class="min-w-0 flex-1">
              <div class="text-[9.5px] tracking-widest text-primary uppercase">QMS plan</div>
              <div class="mt-0.5 text-[11px] text-muted-foreground">
                {data.todos.filter((t) => t.status === "complied").length}/{data.todos.length} sub-steps done
              </div>
            </div>
          {/if}
          <Button
            size="icon-sm"
            variant="ghost"
            class={navigatorCollapsed ? "mx-auto" : ""}
            aria-label={navigatorCollapsed ? "Expand navigator" : "Collapse navigator"}
            onclick={() => (navigatorCollapsed = !navigatorCollapsed)}
          >
            {#if navigatorCollapsed}
              <ChevronsRightIcon class="size-4" />
            {:else}
              <ChevronsLeftIcon class="size-4" />
            {/if}
          </Button>
        </div>

        {#if navigatorCollapsed}
          <div class="flex flex-col items-center gap-1 py-3">
            {#each steps as step, i (step.id)}
              {@const Icon = stepIcon(i)}
              {@const attention = stepNeedsAttention(step.id)}
              <button
                type="button"
                title={step.title}
                onclick={() => {
                  navigatorCollapsed = false;
                  expandedStepId = step.id;
                }}
                class={[
                  "relative flex size-11 items-center justify-center rounded-xl transition-colors hover:bg-accent",
                  expandedStepId === step.id ? "bg-accent text-primary" : "text-muted-foreground",
                ]}
              >
                <Icon class="size-[19px]" />
                {#if attention}
                  <span class="absolute top-2 right-2 size-[7px] rounded-full bg-destructive"></span>
                {/if}
              </button>
            {/each}
          </div>
        {:else}
          <ul>
            {#each steps as step, i (step.id)}
              {@const progress = stepProgress(step.id)}
              {@const pct = progress.total === 0 ? 0 : Math.round((progress.done / progress.total) * 100)}
              {@const attention = stepNeedsAttention(step.id)}
              {@const complete = progress.total > 0 && progress.done === progress.total}
              <li class="border-t border-border first:border-t-0">
                <button
                  type="button"
                  class="flex w-full items-center gap-2.5 p-3 text-left transition-colors hover:bg-accent/60"
                  onclick={() => (expandedStepId = expandedStepId === step.id ? null : step.id)}
                >
                  <span
                    class={[
                      "flex size-7 flex-none items-center justify-center rounded-full font-heading text-[11px] font-medium",
                      complete ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                    ]}
                  >
                    {complete ? "✓" : i + 1}
                  </span>
                  <span class="min-w-0 flex-1">
                    <span class="flex items-center gap-1.5">
                      <span class="block truncate font-heading text-sm font-medium">{step.title}</span>
                      {#if attention}
                        <span class="size-[7px] flex-none rounded-full bg-destructive"></span>
                      {/if}
                    </span>
                    <span class="block text-[11px] text-muted-foreground">{progress.done}/{progress.total}</span>
                  </span>
                  <span class="h-1 w-11 flex-none overflow-hidden rounded-full bg-muted">
                    <span class="block h-full bg-primary" style={`width: ${pct}%`}></span>
                  </span>
                </button>

                {#if expandedStepId === step.id}
                  <ul class="space-y-0.5 pb-2">
                    {#each todosForStep(step.id) as todo (todo.id)}
                      {@const badge = todoBadge(todo)}
                      <li>
                        <button
                          type="button"
                          class={[
                            "ml-10 flex w-[calc(100%-2.5rem-0.75rem)] items-center gap-2 rounded-lg p-2 text-left transition-colors hover:bg-accent",
                            selectedTodoId === todo.id && "bg-accent",
                          ]}
                          onclick={() => selectTodo(todo)}
                        >
                          <span class="min-w-0 flex-1 truncate text-[13px]">{todo.requirement_description}</span>
                          <span class="flex-none font-heading text-[9px] font-medium tracking-wide uppercase {badge.class}">
                            {badge.label}
                          </span>
                        </button>
                      </li>
                    {:else}
                      <li class="ml-10 p-2 text-xs text-muted-foreground">No todos in this step.</li>
                    {/each}
                  </ul>
                {/if}
              </li>
            {/each}
          </ul>
        {/if}
      </nav>

      <!-- Right: selected todo detail -->
      <div class="min-w-0 flex-1 space-y-5">
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

          <Card.Root>
            <Card.Header>
              <div class="flex items-center gap-2.5">
                <span
                  class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-accent text-primary"
                >
                  <MessageSquareIcon class="size-[18px]" />
                </span>
                <Card.Title class="text-base">Discussion</Card.Title>
                <span class="text-xs text-muted-foreground">
                  Non-persistent for now — clears on reload (issue #57)
                </span>
              </div>
            </Card.Header>
            <Card.Content class="space-y-1">
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
              <form
                class="mt-2 flex items-start gap-2.5"
                onsubmit={(event) => {
                  event.preventDefault();
                  submitComment();
                }}
              >
                <textarea
                  class="min-h-[74px] flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm"
                  bind:value={commentDraft}
                  placeholder="Add a comment…"
                ></textarea>
                <Button type="submit" class="flex-none" disabled={!commentDraft.trim()}>Post comment</Button>
              </form>
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

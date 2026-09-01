<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import {
    resolveApiBase,
    createProject,
    uploadAor,
    classifyProject,
    listProcessSteps,
    type Project,
    type ProcessStep,
    type TodoItem,
  } from "$lib/api";
  import { navigate } from "$lib/router.svelte";
  import { guardedNavigate, setWizardDirty } from "$lib/wizardGuard.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  type Phase = "intake" | "classify" | "preview";
  let phase = $state<Phase>("intake");

  let projectName = $state("");
  let project = $state<Project | null>(null);
  let aorFile = $state<File | null>(null);

  let dataSensitivityHigh = $state(false);
  let customerFacing = $state(false);
  let regulatoryExposure = $state(false);

  let pending = $state(false);
  let error = $state<string | null>(null);

  // Step 3: the generated plan preview, grouped by process step (Q41).
  let generatedTodos = $state<TodoItem[]>([]);
  let processSteps = $state<ProcessStep[]>([]);

  // V18 step 3: guards navigation away from the wizard (via Shell's nav,
  // not just this component's own back link) while there's unsaved setup
  // — mirrors ui-reference/'s setupDirty. Nothing left to lose once the
  // plan is generated, so "preview" is never dirty.
  const dirty = $derived(
    phase === "classify" || (phase === "intake" && (projectName.trim() !== "" || aorFile !== null)),
  );
  $effect(() => {
    setWizardDirty(dirty);
    return () => setWizardDirty(false);
  });

  const STEP_LABELS = ["Project details", "Clarification", "QMS plan"] as const;
  const PHASE_INDEX: Record<Phase, number> = { intake: 0, classify: 1, preview: 2 };
  const stepperIndex = $derived(PHASE_INDEX[phase]);
  const answeredCount = $derived(
    [dataSensitivityHigh, customerFacing, regulatoryExposure].filter(Boolean).length,
  );
  const stepCaptions = $derived([
    aorFile
      ? projectName.trim()
        ? "Name and AOR in"
        : "AOR in · name missing"
      : projectName.trim()
        ? "Name in · AOR optional"
        : "Project name needed",
    `${answeredCount} of 3 answered`,
    "Tailored control set",
  ]);
  const heading = $derived((phase === "intake" ? projectName : (project?.name ?? "")).trim() || "New project");

  function todosForStep(stepId: string): TodoItem[] {
    return generatedTodos.filter((todo) => todo.process_step_id === stepId);
  }

  function onAorFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    aorFile = input.files?.[0] ?? null;
  }

  async function startIntake() {
    if (!projectName.trim() || pending) return;
    pending = true;
    error = null;
    try {
      let created = await createProject(apiBase, projectName);
      if (aorFile) {
        created = await uploadAor(apiBase, created.id, aorFile);
      }
      project = created;
      phase = "classify";
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      pending = false;
    }
  }

  async function submitClassification() {
    if (!project || pending) return;
    pending = true;
    error = null;
    try {
      const [result, steps] = await Promise.all([
        classifyProject(apiBase, project.id, {
          data_sensitivity_high: dataSensitivityHigh,
          customer_facing: customerFacing,
          regulatory_exposure: regulatoryExposure,
        }),
        listProcessSteps(apiBase),
      ]);
      project = result.project;
      generatedTodos = result.todos;
      processSteps = steps;
      phase = "preview";
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      pending = false;
    }
  }

  function goToProject() {
    if (!project) return;
    navigate(`/project?id=${project.id}`);
  }
</script>

<main class="mx-auto max-w-2xl space-y-6 p-8">
  <div class="text-[11px] text-muted-foreground">
    <button type="button" class="hover:text-foreground hover:underline" onclick={() => guardedNavigate("/")}>
      Projects
    </button>
    <span> / New project</span>
  </div>

  <header class="space-y-1.5">
    <h1 class="text-[32px] leading-tight font-medium">{heading}</h1>
    <p class="text-[13px] text-muted-foreground">
      Step {stepperIndex + 1} of 3 · {STEP_LABELS[stepperIndex]}
    </p>
  </header>

  <div class="flex items-start rounded-2xl border border-border bg-card px-2 py-4 shadow-sm">
    {#each STEP_LABELS as label, i (label)}
      <div class="flex min-w-0 flex-1 items-start gap-2.5 px-2">
        {#if i > 0}
          <span class="mt-[15px] h-px w-7 min-w-2.5 flex-none" class:bg-primary={i <= stepperIndex} class:bg-border={i > stepperIndex}></span>
        {/if}
        <span
          class={[
            "flex size-[30px] flex-none items-center justify-center rounded-full font-heading text-xs font-medium text-white",
            i <= stepperIndex ? "bg-primary" : "bg-muted-foreground",
            i === stepperIndex && "ring-4 ring-primary/15",
          ]}
        >
          {i < stepperIndex ? "✓" : i + 1}
        </span>
        <span class="min-w-0">
          <span
            class="block font-heading text-xs leading-tight"
            class:font-medium={i === stepperIndex}
            class:text-foreground={i <= stepperIndex}
            class:text-muted-foreground={i > stepperIndex}
          >
            {label}
          </span>
          <span class="mt-0.5 block text-[11px] text-muted-foreground">{stepCaptions[i]}</span>
        </span>
      </div>
    {/each}
  </div>

  {#if phase === "intake"}
    <p class="text-sm text-muted-foreground">
      Name your project and, optionally, upload its intake document (AOR) — we'll read what we can from it
      before you answer the classification questions.
    </p>

    <Card.Root>
      <Card.Content class="space-y-4 pt-6">
        <div class="space-y-1">
          <label class="text-xs text-muted-foreground" for="project-name">Project name</label>
          <Input id="project-name" bind:value={projectName} placeholder="e.g. Customer Portal Revamp" />
        </div>

        <div class="space-y-1">
          <label class="text-xs text-muted-foreground" for="aor-file">
            Intake document (AOR) — optional
          </label>
          <input id="aor-file" type="file" accept=".pdf,.docx,.xlsx" onchange={onAorFileSelected} />
        </div>

        {#if error}
          <p class="text-sm text-destructive">Error: {error}</p>
        {/if}

        <Button onclick={startIntake} disabled={pending || !projectName.trim()}>
          {pending ? "Reading intake document…" : "Continue"}
        </Button>
      </Card.Content>
    </Card.Root>
  {:else if phase === "classify" && project}
    <p class="text-sm text-muted-foreground">
      3 fixed questions (Q8) determine your project's risk tier and generate its compliance todo list.
    </p>

    {#if project.aor_extracted_fields}
      <Card.Root>
        <Card.Content class="space-y-2 pt-6">
          <h2 class="text-sm font-medium">Read from the pack</h2>
          <dl class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
            <dt class="text-muted-foreground">Criticality tier</dt>
            <dd>{project.aor_extracted_fields.criticality_tier}</dd>
            <dt class="text-muted-foreground">Data classification</dt>
            <dd>{project.aor_extracted_fields.data_classification}</dd>
            <dt class="text-muted-foreground">External dependencies</dt>
            <dd>{project.aor_extracted_fields.external_dependencies.join(", ") || "none"}</dd>
            <dt class="text-muted-foreground">In-house rationale</dt>
            <dd>{project.aor_extracted_fields.in_house_rationale}</dd>
          </dl>
        </Card.Content>
      </Card.Root>
    {/if}

    <Card.Root>
      <Card.Content class="space-y-4 pt-6">
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={dataSensitivityHigh} />
          This project handles highly sensitive data
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={customerFacing} />
          This project is customer-facing
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={regulatoryExposure} />
          This project has regulatory exposure
        </label>

        {#if error}
          <p class="text-sm text-destructive">Error: {error}</p>
        {/if}

        <Button onclick={submitClassification} disabled={pending}>
          {pending ? "Classifying…" : "Generate my compliance plan"}
        </Button>
      </Card.Content>
    </Card.Root>
  {:else if phase === "preview" && project}
    <p class="text-sm text-muted-foreground">
      Classified as <strong>{project.risk_tier} tier</strong> — {generatedTodos.length} compliance
      todo{generatedTodos.length === 1 ? "" : "s"} generated, grouped by process step.
    </p>

    <div class="space-y-3">
      {#each processSteps as step (step.id)}
        {@const stepTodos = todosForStep(step.id)}
        {#if stepTodos.length > 0}
          <Card.Root>
            <Card.Header>
              <Card.Title class="text-base">{step.title}</Card.Title>
              <Card.Description>{stepTodos.length} todo{stepTodos.length === 1 ? "" : "s"}</Card.Description>
            </Card.Header>
            <Card.Content>
              <ul class="space-y-2 text-sm">
                {#each stepTodos as todo (todo.id)}
                  <li class="flex items-start justify-between gap-3 border-t border-border pt-2 first:border-0 first:pt-0">
                    <span>{todo.requirement_description}</span>
                    {#if todo.approval_state !== "not_required"}
                      <Badge variant="outline" class="shrink-0">{todo.approval_authority}</Badge>
                    {/if}
                  </li>
                {/each}
              </ul>
            </Card.Content>
          </Card.Root>
        {/if}
      {/each}
    </div>

    <Button onclick={goToProject}>Go to project</Button>
  {/if}
</main>

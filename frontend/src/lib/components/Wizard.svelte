<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import { resolveApiBase, createProject, uploadAor, classifyProject, type Project } from "$lib/api";

  const apiBase = resolveApiBase(import.meta.env);

  type Phase = "intake" | "classify";
  let phase = $state<Phase>("intake");

  let projectName = $state("");
  let project = $state<Project | null>(null);
  let aorFile = $state<File | null>(null);

  let dataSensitivityHigh = $state(false);
  let customerFacing = $state(false);
  let regulatoryExposure = $state(false);

  let pending = $state(false);
  let error = $state<string | null>(null);

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
      const result = await classifyProject(apiBase, project.id, {
        data_sensitivity_high: dataSensitivityHigh,
        customer_facing: customerFacing,
        regulatory_exposure: regulatoryExposure,
      });
      window.location.assign(`/project?id=${result.project.id}`);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      pending = false;
    }
  }
</script>

<main class="mx-auto max-w-xl space-y-6 p-8">
  {#if phase === "intake"}
    <header class="space-y-1">
      <h1 class="text-2xl font-medium">Start a new project</h1>
      <p class="text-sm text-muted-foreground">
        Name your project and, optionally, upload its intake document (AOR) — we'll
        read what we can from it before you answer the classification questions.
      </p>
    </header>

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
  {:else if project}
    <header class="space-y-1">
      <h1 class="text-2xl font-medium">Classify {project.name}</h1>
      <p class="text-sm text-muted-foreground">
        3 fixed questions (Q8) determine your project's risk tier and generate its
        compliance todo list.
      </p>
    </header>

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
  {/if}
</main>

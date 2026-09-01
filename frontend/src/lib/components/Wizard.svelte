<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import { resolveApiBase, createProject } from "$lib/api";

  const apiBase = resolveApiBase(import.meta.env);

  let projectName = $state("");
  let dataSensitivityHigh = $state(false);
  let customerFacing = $state(false);
  let regulatoryExposure = $state(false);
  let pending = $state(false);
  let error = $state<string | null>(null);

  async function submit() {
    if (!projectName.trim() || pending) return;
    pending = true;
    error = null;
    try {
      const result = await createProject(apiBase, projectName, {
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
  <header class="space-y-1">
    <h1 class="text-2xl font-medium">Classify your project</h1>
    <p class="text-sm text-muted-foreground">
      3 fixed questions (Q8) determine your project's risk tier and generate its
      compliance todo list.
    </p>
  </header>

  <Card.Root>
    <Card.Content class="space-y-4 pt-6">
      <div class="space-y-1">
        <label class="text-xs text-muted-foreground" for="project-name">Project name</label>
        <Input id="project-name" bind:value={projectName} placeholder="e.g. Customer Portal Revamp" />
      </div>

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

      <Button onclick={submit} disabled={pending || !projectName.trim()}>
        {pending ? "Classifying…" : "Generate my compliance plan"}
      </Button>
    </Card.Content>
  </Card.Root>
</main>

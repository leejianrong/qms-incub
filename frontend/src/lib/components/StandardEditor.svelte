<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import {
    resolveApiBase,
    createClause,
    createRequirement,
    createStandard,
    listClauses,
    listRequirements,
    listStandards,
    type Clause,
    type Requirement,
    type RiskTier,
    type Standard,
  } from "$lib/api";

  const apiBase = resolveApiBase(import.meta.env);

  let standards = $state<Standard[]>([]);
  let clausesByStandard = $state<Record<string, Clause[]>>({});
  let requirementsByClause = $state<Record<string, Requirement[]>>({});
  let error = $state<string | null>(null);

  let standardName = $state("");
  let standardDescription = $state("");

  const clauseText: Record<string, string> = $state({});
  const requirementDescription: Record<string, string> = $state({});
  const requirementTiers: Record<string, Record<RiskTier, boolean>> = $state({});

  async function refreshStandards() {
    standards = await listStandards(apiBase);
    for (const standard of standards) {
      clausesByStandard[standard.id] = await listClauses(apiBase, standard.id);
      for (const clause of clausesByStandard[standard.id]) {
        requirementsByClause[clause.id] = await listRequirements(apiBase, clause.id);
      }
    }
  }

  refreshStandards().catch((err) => (error = err instanceof Error ? err.message : String(err)));

  async function addStandard() {
    if (!standardName.trim()) return;
    try {
      await createStandard(apiBase, standardName, standardDescription);
      standardName = "";
      standardDescription = "";
      await refreshStandards();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }

  async function addClause(standardId: string) {
    const text = clauseText[standardId];
    if (!text?.trim()) return;
    try {
      await createClause(apiBase, standardId, (clausesByStandard[standardId]?.length ?? 0) + 1, text);
      clauseText[standardId] = "";
      await refreshStandards();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }

  async function addRequirement(clauseId: string) {
    const description = requirementDescription[clauseId];
    const tiers = requirementTiers[clauseId] ?? { low: false, medium: false, high: false };
    const riskTiers = (Object.keys(tiers) as RiskTier[]).filter((tier) => tiers[tier]);
    if (!description?.trim() || riskTiers.length === 0) return;
    try {
      await createRequirement(apiBase, clauseId, description, riskTiers);
      requirementDescription[clauseId] = "";
      requirementTiers[clauseId] = { low: false, medium: false, high: false };
      await refreshStandards();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
  }
</script>

<main class="mx-auto max-w-3xl space-y-6 p-8">
  <header class="space-y-1">
    <h1 class="text-2xl font-medium">Compliance Standard editor</h1>
    <p class="text-sm text-muted-foreground">
      QA-author tool. Standard &gt; Clause &gt; Requirement is user-authored data,
      not a hardcoded regulatory schema (ADR-0008).
    </p>
  </header>

  {#if error}
    <p class="text-sm text-destructive">Error: {error}</p>
  {/if}

  <Card.Root>
    <Card.Header>
      <Card.Title>New Standard</Card.Title>
    </Card.Header>
    <Card.Content class="flex flex-wrap gap-3">
      <Input placeholder="Standard name" bind:value={standardName} class="max-w-xs" />
      <Input placeholder="Description" bind:value={standardDescription} class="max-w-xs" />
      <Button onclick={addStandard}>Add Standard</Button>
    </Card.Content>
  </Card.Root>

  {#each standards as standard (standard.id)}
    <Card.Root>
      <Card.Header>
        <Card.Title>{standard.name}</Card.Title>
        <Card.Description>{standard.description}</Card.Description>
      </Card.Header>
      <Card.Content class="space-y-4">
        {#each clausesByStandard[standard.id] ?? [] as clause (clause.id)}
          <div class="rounded-md border border-border p-3 space-y-2">
            <p class="text-sm font-medium">Clause {clause.ordering}: {clause.text}</p>
            <ul class="space-y-1">
              {#each requirementsByClause[clause.id] ?? [] as requirement (requirement.id)}
                <li class="flex items-center gap-2 text-sm">
                  <span>{requirement.description}</span>
                  {#each requirement.risk_tiers as tier (tier)}
                    <Badge variant="outline">{tier}</Badge>
                  {/each}
                </li>
              {/each}
            </ul>
            <div class="flex flex-wrap items-center gap-2">
              <Input
                placeholder="Requirement description"
                bind:value={requirementDescription[clause.id]}
                class="max-w-xs"
              />
              {#each ["low", "medium", "high"] as const as tier (tier)}
                <label class="flex items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={requirementTiers[clause.id]?.[tier] ?? false}
                    onchange={(e) => {
                      requirementTiers[clause.id] ??= { low: false, medium: false, high: false };
                      requirementTiers[clause.id][tier] = (e.target as HTMLInputElement).checked;
                    }}
                  />
                  {tier}
                </label>
              {/each}
              <Button variant="secondary" onclick={() => addRequirement(clause.id)}>
                Add Requirement
              </Button>
            </div>
          </div>
        {/each}
        <div class="flex gap-2">
          <Input placeholder="New clause text" bind:value={clauseText[standard.id]} class="max-w-xs" />
          <Button variant="secondary" onclick={() => addClause(standard.id)}>Add Clause</Button>
        </div>
      </Card.Content>
    </Card.Root>
  {/each}
</main>

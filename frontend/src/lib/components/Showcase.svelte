<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import * as Select from "$lib/components/ui/select/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Tabs from "$lib/components/ui/tabs/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";

  const riskTiers = ["Low", "Medium", "High"];
  let selectedTier = $state("Medium");
</script>

<main class="mx-auto max-w-3xl space-y-8 p-8">
  <header class="space-y-1">
    <h1 class="text-2xl font-medium">Component showcase</h1>
    <p class="text-sm text-muted-foreground">
      shadcn-svelte primitives themed against ui-reference/QMS Console.dc.html's
      design tokens (ADR-0013). Local-only reference route, not linked from the
      product nav.
    </p>
  </header>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Buttons</h2>
    <div class="flex flex-wrap gap-3">
      <Button variant="default">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="destructive">Destructive</Button>
      <Button disabled>Disabled</Button>
    </div>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Inputs &amp; badges</h2>
    <div class="flex flex-wrap items-center gap-3">
      <Input placeholder="Project name" class="max-w-xs" />
      <Badge>Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="outline">Outline</Badge>
      <Badge variant="destructive">Destructive</Badge>
    </div>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Select</h2>
    <Select.Root type="single" bind:value={selectedTier}>
      <Select.Trigger class="max-w-xs">
        {selectedTier ?? "Choose a risk tier"}
      </Select.Trigger>
      <Select.Content>
        {#each riskTiers as tier (tier)}
          <Select.Item value={tier} label={tier}>{tier}</Select.Item>
        {/each}
      </Select.Content>
    </Select.Root>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Card</h2>
    <Card.Root class="max-w-sm">
      <Card.Header>
        <Card.Title>Data retention policy</Card.Title>
        <Card.Description>Standard &gt; Clause &gt; Requirement</Card.Description>
      </Card.Header>
      <Card.Content>
        <p class="text-sm text-muted-foreground">
          Todo items trace back to a Requirement, which traces back to a Clause
          and a Standard (ADR-0008).
        </p>
      </Card.Content>
      <Card.Footer>
        <Badge variant="outline">High tier</Badge>
      </Card.Footer>
    </Card.Root>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Tabs</h2>
    <Tabs.Root value="pending" class="max-w-sm">
      <Tabs.List>
        <Tabs.Trigger value="pending">Pending</Tabs.Trigger>
        <Tabs.Trigger value="complied">Complied</Tabs.Trigger>
      </Tabs.List>
      <Tabs.Content value="pending">3 todos pending.</Tabs.Content>
      <Tabs.Content value="complied">2 todos complied.</Tabs.Content>
    </Tabs.Root>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Dropdown menu &amp; dialog</h2>
    <div class="flex flex-wrap gap-3">
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button variant="outline" {...props}>Actions</Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content>
          <DropdownMenu.Item>Upload artifact</DropdownMenu.Item>
          <DropdownMenu.Item>View requirement</DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Root>

      <Dialog.Root>
        <Dialog.Trigger>
          {#snippet child({ props })}
            <Button {...props}>Open dialog</Button>
          {/snippet}
        </Dialog.Trigger>
        <Dialog.Content>
          <Dialog.Header>
            <Dialog.Title>Self-attest compliance</Dialog.Title>
            <Dialog.Description>
              Uploading a file marks this todo item Complied.
            </Dialog.Description>
          </Dialog.Header>
        </Dialog.Content>
      </Dialog.Root>
    </div>
  </section>
</main>

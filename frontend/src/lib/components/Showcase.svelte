<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import * as Select from "$lib/components/ui/select/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Tabs from "$lib/components/ui/tabs/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import * as Avatar from "$lib/components/ui/avatar/index.js";
  import * as Tooltip from "$lib/components/ui/tooltip/index.js";
  import * as Sheet from "$lib/components/ui/sheet/index.js";
  import * as Popover from "$lib/components/ui/popover/index.js";

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

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Progress</h2>
    <div class="max-w-sm space-y-3">
      <Progress value={30} />
      <Progress value={65} />
      <Progress value={100} />
    </div>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Avatar</h2>
    <div class="flex flex-wrap items-center gap-3">
      <Avatar.Root size="sm">
        <Avatar.Fallback>PM</Avatar.Fallback>
      </Avatar.Root>
      <Avatar.Root>
        <Avatar.Fallback>KA</Avatar.Fallback>
      </Avatar.Root>
      <Avatar.Root size="lg">
        <Avatar.Fallback>QA</Avatar.Fallback>
      </Avatar.Root>
    </div>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Tooltip</h2>
    <Tooltip.Provider>
      <Tooltip.Root>
        <Tooltip.Trigger>
          {#snippet child({ props })}
            <Button variant="outline" {...props}>Hover for detail</Button>
          {/snippet}
        </Tooltip.Trigger>
        <Tooltip.Content>Retrieval mode: BM25 (sparse lexical)</Tooltip.Content>
      </Tooltip.Root>
    </Tooltip.Provider>
  </section>

  <section class="space-y-3">
    <h2 class="text-lg font-medium">Sheet &amp; popover</h2>
    <div class="flex flex-wrap gap-3">
      <Sheet.Root>
        <Sheet.Trigger>
          {#snippet child({ props })}
            <Button variant="outline" {...props}>Open sheet</Button>
          {/snippet}
        </Sheet.Trigger>
        <Sheet.Content>
          <Sheet.Header>
            <Sheet.Title>Discussion thread</Sheet.Title>
            <Sheet.Description>
              Slide-in panel reference for a floating chat widget or a
              todo-detail comment thread.
            </Sheet.Description>
          </Sheet.Header>
        </Sheet.Content>
      </Sheet.Root>

      <Popover.Root>
        <Popover.Trigger>
          {#snippet child({ props })}
            <Button variant="outline" {...props}>Open popover</Button>
          {/snippet}
        </Popover.Trigger>
        <Popover.Content>
          <p class="text-sm text-muted-foreground">
            Small anchored overlay, e.g. for a chat launcher or a quick
            reference card.
          </p>
        </Popover.Content>
      </Popover.Root>
    </div>
  </section>
</main>

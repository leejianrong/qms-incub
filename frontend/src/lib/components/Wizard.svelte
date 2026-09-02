<script lang="ts">
  import FileTextIcon from "@lucide/svelte/icons/file-text";
  import UploadIcon from "@lucide/svelte/icons/upload";
  import CircleCheckIcon from "@lucide/svelte/icons/circle-check";
  import ListIcon from "@lucide/svelte/icons/list";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { resolveApiBase, createProject, uploadAor, type Project } from "$lib/api";
  import { navigate } from "$lib/router.svelte";
  import { guardedNavigate, setWizardDirty } from "$lib/wizardGuard.svelte";
  import { saveWizardPlan } from "$lib/wizardPlan";

  const apiBase = resolveApiBase(import.meta.env);

  // The clarification step (Q8's 3 questions) is skipped in this flow —
  // step 1 goes straight to the generated QMS plan, and the plan itself is
  // picked client-side from the AOR filename (see PLAN_A / PLAN_B below).
  type Phase = "intake" | "preview";
  let phase = $state<Phase>("intake");

  let projectName = $state("");
  let targetDate = $state("");
  let project = $state<Project | null>(null);
  let aorFile = $state<File | null>(null);
  let dragOver = $state(false);
  let fileInput = $state<HTMLInputElement | null>(null);

  // Client-side reservation only — the backend has no deployment-date or
  // record-code field (POST /projects takes just {name}); these mirror
  // ui-reference/QMS Console.dc.html's create wizard, where both are
  // generated in the browser at step 1.
  const recordCode = `SW-${new Date().getFullYear()}-${100 + Math.floor(Math.random() * 900)}`;

  // Step 3: the plan is chosen by the AOR filename — a pack whose name
  // contains "-1" / "_1" gets the iterative control set, anything else
  // gets the staged one. Each step carries a " · "-joined sub-step line
  // (rendered under the title, like ui-reference/QMS Console.dc.html's
  // "Your QMS plan" card). Frontend-only demo wiring; the real generator
  // is backend work that isn't in this slice.
  type PlanStep = { code: string; title: string; subs: string };

  const STEP_P002 = "Open the project record · Agree scope, schedule and resources · Project management plan approval";
  const STEP_P006 = "Run the acceptance test campaign · Resolve defects and waivers · Acceptance authority sign-off";
  const STEP_P007 = "Release and installation planning · Cut over to operations · Handover to the support organisation";

  const PLAN_A: PlanStep[] = [
    { code: "P002", title: "Project Planning", subs: STEP_P002 },
    {
      code: "P009",
      title: "Iteration Planning",
      subs: "Groom and size the backlog · Commit the iteration goal · Confirm capacity and dependencies",
    },
    {
      code: "P009",
      title: "Iterative Review",
      subs: "Demonstrate the increment · Capture stakeholder feedback · Update the backlog and risk log",
    },
    { code: "P006", title: "System Acceptance", subs: STEP_P006 },
    { code: "P007", title: "Deployment & Transition to O&S", subs: STEP_P007 },
  ];
  const PLAN_B: PlanStep[] = [
    { code: "P002", title: "Project Planning", subs: STEP_P002 },
    {
      code: "P003",
      title: "System Definition",
      subs: "Capture stakeholder needs · Baseline the system requirements · Requirements review and sign-off",
    },
    {
      code: "P004",
      title: "System Design",
      subs: "Develop the architecture · Allocate requirements to components · Preliminary and critical design reviews",
    },
    {
      code: "P005",
      title: "Development, Test and Evaluation",
      subs: "Implement to the design baseline · Unit and integration testing · Verification against requirements",
    },
    { code: "P006", title: "System Acceptance", subs: STEP_P006 },
    { code: "P007", title: "Deployment & Transition to O&S", subs: STEP_P007 },
  ];
  const planVariant = $derived(/[_-]1\b/.test(aorFile?.name ?? "") ? "a" : "b");
  const planSteps = $derived(planVariant === "a" ? PLAN_A : PLAN_B);

  function subCount(subs: string): number {
    return subs.split(" · ").filter(Boolean).length;
  }
  const totalSubSteps = $derived(planSteps.reduce((n, s) => n + subCount(s.subs), 0));

  // V18 step 3: guards navigation away from the wizard (via Shell's nav,
  // not just this component's own back link) while there's unsaved setup.
  // Nothing left to lose once the plan is generated, so "preview" is never
  // dirty.
  const dirty = $derived(
    phase === "intake" &&
      (projectName.trim() !== "" || targetDate !== "" || aorFile !== null),
  );
  $effect(() => {
    setWizardDirty(dirty);
    return () => setWizardDirty(false);
  });

  const STEP_LABELS = ["Project details", "Clarification", "QMS plan"] as const;
  const PHASE_INDEX: Record<Phase, number> = { intake: 0, preview: 2 };
  const stepperIndex = $derived(PHASE_INDEX[phase]);

  const detailsOk = $derived(projectName.trim() !== "" && targetDate !== "" && aorFile !== null);
  const stepCaptions = $derived([
    aorFile
      ? detailsOk
        ? "Name, date and AOR in"
        : "AOR in · details missing"
      : "Name, date and AOR",
    "Set from the AOR",
    "Tailored control set",
  ]);
  const heading = $derived(
    (phase === "intake" ? projectName : (project?.name ?? projectName)).trim() || "New project",
  );

  const planSummary = $derived(
    `${totalSubSteps} sub-steps · ${planSteps.length} step${planSteps.length === 1 ? "" : "s"}`,
  );
  const tailoring = $derived([
    `Control set tailored from ${aorFile?.name ?? "the AOR pack"}`,
    planVariant === "a"
      ? "Iterative delivery — iteration planning and review recur each cycle"
      : "Staged delivery — definition, design and development run in sequence",
    `${totalSubSteps} sub-steps across ${planSteps.length} process steps, closing at deployment and transition to O&S`,
  ]);

  function formatSize(bytes: number): string {
    if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }

  function setAorFile(file: File | null | undefined) {
    aorFile = file ?? null;
  }

  function onAorFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    setAorFile(input.files?.[0]);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    setAorFile(event.dataTransfer?.files?.[0]);
  }

  // Kicked off when we reach the preview so the project row exists by the
  // time the user clicks "Create". `project` is set as soon as
  // createProject returns (before the slower AOR extraction) so navigation
  // never has to wait on Docling/the LLM; finish() awaits this promise so
  // a fast click can't race ahead of it and fall back to the home page.
  let registration = $state<Promise<void> | null>(null);
  let finishing = $state(false);

  function planForDetail() {
    return planSteps.map((s) => ({
      code: s.code,
      title: s.title,
      subs: s.subs.split(" · ").filter(Boolean),
    }));
  }

  function generatePlan() {
    if (!projectName.trim() || !aorFile) return;
    phase = "preview";
    if (project || registration) return;
    const file = aorFile;
    registration = (async () => {
      try {
        let created = await createProject(apiBase, projectName);
        project = created;
        saveWizardPlan(created.id, { name: projectName, steps: planForDetail() });
        if (!created.aor_filename) {
          try {
            created = await uploadAor(apiBase, created.id, file);
            project = created;
          } catch (err) {
            console.warn("Wizard: AOR extraction failed, project still created —", err);
          }
        }
      } catch (err) {
        console.warn("Wizard: project registration failed —", err);
      }
    })();
  }

  async function finish() {
    finishing = true;
    if (registration) await registration;
    finishing = false;
    if (project) navigate(`/project?id=${project.id}`);
    else navigate("/");
  }

  const footer = $derived.by(() => {
    if (phase === "intake") {
      return {
        prevDisabled: true,
        onPrev: () => {},
        nextLabel: "Next",
        nextDisabled: !projectName.trim() || !aorFile,
        onNext: generatePlan,
      };
    }
    return {
      prevDisabled: finishing,
      onPrev: () => {
        phase = "intake";
      },
      nextLabel: finishing ? "Creating…" : "Create",
      nextDisabled: finishing,
      onNext: finish,
    };
  });
</script>

<main class="pb-32">
  <header class="border-b border-border bg-card px-8 pt-8 pb-6">
    <div class="text-[11px] text-muted-foreground">
      <button
        type="button"
        class="hover:text-foreground hover:underline"
        onclick={() => guardedNavigate("/")}
      >
        Projects
      </button>
      <span> / New project</span>
    </div>
    <h1 class="mt-1 text-[32px] leading-tight font-medium">{heading}</h1>
    <p class="mt-2 text-[13px] text-muted-foreground">
      Step {stepperIndex + 1} of 3 · {STEP_LABELS[stepperIndex]}
    </p>
  </header>

  <div class="px-8 pt-7 pb-6">
    <div class="flex items-start rounded-2xl border border-border bg-card px-4 py-5 shadow-sm">
      {#each STEP_LABELS as label, i (label)}
        <div class="flex min-w-0 flex-1 items-start gap-2.5 px-2">
          {#if i > 0}
            <span
              class="mt-[15px] h-px w-7 min-w-2.5 flex-none"
              class:bg-primary={i <= stepperIndex}
              class:bg-border={i > stepperIndex}
            ></span>
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
  </div>

  {#if phase === "intake"}
    <div class="space-y-5 px-8">
      <section class="rounded-2xl border border-border bg-card px-6 py-6 shadow-sm">
        <div class="mb-4 flex items-center gap-3">
          <span
            class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-accent text-accent-foreground"
          >
            <FileTextIcon class="size-[18px]" />
          </span>
          <h2 class="text-[17px] font-medium">Project details</h2>
        </div>
        <div class="grid max-w-3xl gap-5 sm:grid-cols-[minmax(0,1fr)_240px]">
          <div class="space-y-1">
            <label class="text-xs text-muted-foreground" for="project-name">Project name</label>
            <Input id="project-name" bind:value={projectName} placeholder="e.g. Sentinel Ops Portal" />
          </div>
          <div class="space-y-1">
            <label class="text-xs text-muted-foreground" for="target-date">
              Targeted deployment date
            </label>
            <Input id="target-date" type="date" bind:value={targetDate} />
          </div>
        </div>
        <p class="mt-3 text-xs text-muted-foreground">
          Record code {recordCode} is reserved for this project.
        </p>
      </section>

      <section class="rounded-2xl border border-border bg-card px-6 py-6 shadow-sm">
        <div class="mb-1.5 flex items-center gap-3">
          <span
            class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-accent text-accent-foreground"
          >
            <UploadIcon class="size-[18px]" />
          </span>
          <h2 class="text-[17px] font-medium">Upload the AOR</h2>
          {#if aorFile}
            <Badge variant="secondary" class="ml-auto tracking-wide uppercase">Uploaded</Badge>
          {:else}
            <Badge variant="destructive" class="ml-auto gap-1.5 tracking-wide uppercase">
              <span class="size-2 rounded-full bg-destructive"></span>
              Required
            </Badge>
          {/if}
        </div>
        <p class="mb-3.5 text-[13px] text-muted-foreground">
          The Approval of Requirement pack states what is being built and why in-house. The QMS reads
          it to work out which approvals and controls apply, so the plan cannot be generated without
          it.
        </p>

        <button
          type="button"
          onclick={() => fileInput?.click()}
          ondragover={(e) => {
            e.preventDefault();
            dragOver = true;
          }}
          ondragleave={() => (dragOver = false)}
          ondrop={onDrop}
          class={[
            "flex w-full items-center gap-4 rounded-2xl border-2 border-dashed px-6 py-6 text-left transition-colors",
            aorFile
              ? "border-border bg-[var(--color-surface)]"
              : "border-primary bg-accent hover:border-[var(--color-accent-600)]",
            dragOver && "border-[var(--color-accent-600)]",
          ]}
        >
          <span
            class="flex size-[46px] flex-none items-center justify-center rounded-full border border-border bg-white text-primary"
          >
            <UploadIcon class="size-[21px]" />
          </span>
          <span class="min-w-0">
            <span class="block font-heading text-[15.5px] font-medium">
              Drop the AOR here, or click to browse
            </span>
            <span class="mt-1 block text-xs text-muted-foreground">
              PDF, DOCX or XLSX · max 25 MB · a draft is fine at this stage
            </span>
          </span>
        </button>
        <input
          bind:this={fileInput}
          type="file"
          accept=".pdf,.docx,.xlsx"
          class="hidden"
          onchange={onAorFileSelected}
        />

        {#if aorFile}
          <div class="mt-3.5 flex items-center gap-3 rounded-xl border border-border px-4 py-3.5">
            <div class="min-w-0 flex-1">
              <div class="truncate font-heading text-sm font-medium">{aorFile.name}</div>
              <div class="text-[11px] text-muted-foreground">
                {formatSize(aorFile.size)} · {aorFile.type || "file"}
              </div>
            </div>
            <Button variant="ghost" size="sm" onclick={() => setAorFile(null)}>Remove</Button>
          </div>
        {/if}
      </section>
    </div>
  {:else if phase === "preview"}
    <div class="space-y-5 px-8">
      <section class="rounded-2xl border border-border bg-card px-6 py-6 shadow-sm">
        <div class="mb-2 flex items-center gap-3">
          <span
            class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-accent text-accent-foreground"
          >
            <CircleCheckIcon class="size-[18px]" />
          </span>
          <h2 class="text-[17px] font-medium">Applied to your process</h2>
        </div>
        {#each tailoring as line, i (i)}
          <div class="flex gap-3 border-t border-border py-2.5 text-[13.5px]">
            <span class="flex-none font-heading font-medium text-primary">•</span>
            <span>{line}</span>
          </div>
        {/each}
      </section>

      <section class="rounded-2xl border border-border bg-card px-6 py-6 shadow-sm">
        <div class="mb-3 flex items-center gap-3">
          <span
            class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-accent text-accent-foreground"
          >
            <ListIcon class="size-[18px]" />
          </span>
          <h2 class="text-[17px] font-medium">Your QMS plan</h2>
          <span class="ml-auto text-xs text-muted-foreground">{planSummary}</span>
        </div>
        {#each planSteps as step, i (i)}
          <div class="flex items-start gap-3.5 border-t border-border py-3">
            <span
              class="mt-0.5 flex size-7 flex-none items-center justify-center rounded-full bg-accent font-heading text-xs font-medium text-accent-foreground"
            >
              {i + 1}
            </span>
            <span class="min-w-0 flex-1">
              <span class="block font-heading text-[14.5px] font-medium">
                {step.code}: {step.title}
              </span>
              <span class="mt-0.5 block text-xs leading-relaxed text-muted-foreground">
                {step.subs}
              </span>
            </span>
            <span class="mt-0.5 flex-none text-xs text-muted-foreground">
              {subCount(step.subs)} sub-steps
            </span>
          </div>
        {/each}
      </section>
    </div>
  {/if}

  <div
    class="relative z-40 mt-6 flex items-center justify-end gap-3 px-8"
  >
    <Button variant="ghost" disabled={footer.prevDisabled} onclick={footer.onPrev}>Previous</Button>
    <Button disabled={footer.nextDisabled} onclick={footer.onNext}>{footer.nextLabel}</Button>
  </div>
</main>

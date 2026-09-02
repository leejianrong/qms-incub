// The create-project wizard generates its step-3 "QMS plan" entirely
// client-side from the AOR filename (Wizard.svelte's PLAN_A / PLAN_B) —
// the backend classify step isn't wired into this flow, so a freshly
// created project has no todos and its risk_tier stays null forever. This
// stashes that plan (in sessionStorage, keyed by project id) so
// ProjectDetail.svelte, ProjectsDashboard.svelte, Favourites.svelte, and
// Shell.svelte's notifications can all treat a project with a stashed plan
// as "classified" for display purposes even though risk_tier is null.
// Survives the navigation and a page reload in the SAME browser tab;
// cleared when the tab closes, and never visible from a different tab
// (opening the project via a shared link, e.g.) since sessionStorage is
// per-tab — a known gap of this frontend-only demo wiring, not a real
// classification, see AGENTS.md's V13 row.

export interface WizardPlanStep {
  code: string;
  title: string;
  subs: string[];
}

export interface StoredWizardPlan {
  name: string;
  steps: WizardPlanStep[];
}

const keyFor = (projectId: string) => `wizardPlan:${projectId}`;

export function saveWizardPlan(projectId: string, plan: StoredWizardPlan): void {
  try {
    sessionStorage.setItem(keyFor(projectId), JSON.stringify(plan));
  } catch {
    // sessionStorage unavailable (private mode, quota) — the project page
    // just falls back to the backend navigator.
  }
}

export function loadWizardPlan(projectId: string): StoredWizardPlan | null {
  if (!projectId) return null;
  try {
    const raw = sessionStorage.getItem(keyFor(projectId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredWizardPlan;
    if (!parsed || !Array.isArray(parsed.steps)) return null;
    return parsed;
  } catch {
    return null;
  }
}

// Shared by every view that renders a wizard-plan-backed project as if it
// had real backend todos/process-steps (ProjectDetail's navigator,
// ProjectsDashboard/Favourites's cards) — kept in one place so they can't
// drift on id shape or field defaults.
import type { ProcessStep, TodoItem } from "./api";

export function wizardPlanToSteps(plan: StoredWizardPlan): ProcessStep[] {
  return plan.steps.map((s, i) => ({ id: `wiz:${i}`, title: `${s.code}: ${s.title}`, ordering: i }));
}

export function wizardPlanToTodos(projectId: string, plan: StoredWizardPlan): TodoItem[] {
  return plan.steps.flatMap((s, si) =>
    s.subs.map((sub, bi) => ({
      id: `wiz:${si}:${bi}`,
      project_id: projectId,
      requirement_id: `wiz:${si}:${bi}`,
      requirement_description: sub,
      clause_text: `${s.code}: ${s.title}`,
      standard_name: "QMS plan",
      status: "pending" as const,
      process_step_id: `wiz:${si}`,
      approval_state: "not_required" as const,
      approval_authority: "",
      sla_target: null,
      decided_at: null,
    })),
  );
}

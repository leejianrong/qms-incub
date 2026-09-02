// The create-project wizard generates its step-3 "QMS plan" entirely
// client-side from the AOR filename (Wizard.svelte's PLAN_A / PLAN_B) —
// the backend classify step isn't wired into this flow, so a freshly
// created project has no todos. This stashes that plan (in sessionStorage,
// keyed by project id) so ProjectDetail.svelte can render the same steps
// and sub-steps in its navigator after "Create" navigates there. Survives
// the navigation and a page reload; cleared when the tab closes.

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

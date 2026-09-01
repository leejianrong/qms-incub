// V18 step 3: guards navigation away from the create-project wizard while
// it holds unsaved setup (name typed, AOR uploaded, or clarification
// questions answered but the plan not yet generated) — mirrors
// ui-reference/'s navGuard/discardTo. Shared module state (not local to
// Wizard.svelte) because the thing that has to be intercepted is
// navigation initiated from Shell's header nav, not just a link inside
// the wizard itself.
import { navigate as rawNavigate } from "./router.svelte";

let dirty = $state(false);
let pendingPath = $state<string | null>(null);

export function isWizardDirty(): boolean {
  return dirty;
}

export function setWizardDirty(value: boolean): void {
  dirty = value;
}

export function getPendingNavigation(): string | null {
  return pendingPath;
}

export function cancelPendingNavigation(): void {
  pendingPath = null;
}

// Takes an injectable navigate function (defaulting to the real router)
// so this is testable without mocking the router module — same pattern
// as api.ts's fetchImpl parameter.
export function guardedNavigate(path: string, navigateImpl: (path: string) => void = rawNavigate): void {
  if (dirty) {
    pendingPath = path;
  } else {
    navigateImpl(path);
  }
}

export function confirmPendingNavigation(navigateImpl: (path: string) => void = rawNavigate): void {
  const path = pendingPath;
  pendingPath = null;
  dirty = false;
  if (path !== null) navigateImpl(path);
}

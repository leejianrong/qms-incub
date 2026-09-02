// V18 step 2: pure, unit-tested view-model logic for the ProjectsDashboard
// card grid — mirrors ui-reference/'s projectRows()/stats computation, but
// adapted to our real Project/TodoItem/ProcessStep shape rather than the
// reference's richer (fictional) sub-step/approvals-queue model. Kept out
// of the Svelte component so the derivation logic is testable without
// rendering.
import type { Project, TodoItem, ProcessStep } from "./api";

export type ProjectCardStatus = "draft" | "needs_action" | "with_approver" | "complete" | "in_progress";

export type ProjectCardCellState = "complied" | "submitted" | "returned" | "not_started";

export interface ProjectCardAlert {
  kind: "returned" | "awaiting_approval";
  title: string;
  authority: string;
  waitingLabel: string;
}

export interface ProjectCardViewModel {
  id: string;
  code: string;
  name: string;
  isDraft: boolean;
  status: ProjectCardStatus;
  pct: number;
  cells: ProjectCardCellState[];
  stepLabel: string;
  alert: ProjectCardAlert | null;
}

export function projectCode(id: string): string {
  return "PRJ-" + id.replace(/-/g, "").slice(0, 6).toUpperCase();
}

// sla_target is an ISO datetime; render it as a short target date rather
// than dumping the raw string into the card.
export function formatSlaTarget(slaTarget: string | null): string {
  if (!slaTarget) return "just submitted";
  const date = new Date(slaTarget);
  if (Number.isNaN(date.getTime())) return "just submitted";
  // Fixed to UTC rather than the viewer's local timezone so this is
  // deterministic (and so a date near midnight doesn't roll differently
  // depending on where the viewer — or a test runner — happens to be).
  return "due " + date.toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
}

export function buildProjectCard(
  project: Project,
  todos: TodoItem[],
  steps: ProcessStep[],
  // True when this project's todos/steps come from the create-wizard's
  // client-only stashed plan rather than a real backend classification
  // (wizardPlan.ts) — risk_tier is still null in that case, but the
  // project isn't an empty draft, so it shouldn't render as one.
  hasWizardPlan = false,
): ProjectCardViewModel {
  const isDraft = project.risk_tier === null && !hasWizardPlan;
  const returnedTodo = todos.find((t) => t.approval_state === "returned") ?? null;
  const submittedTodo = todos.find((t) => t.approval_state === "submitted") ?? null;

  const total = todos.length;
  const done = todos.filter((t) => t.status === "complied").length;
  const pct = total === 0 ? 0 : Math.round((done / total) * 100);

  const status: ProjectCardStatus = isDraft
    ? "draft"
    : returnedTodo
      ? "needs_action"
      : submittedTodo
        ? "with_approver"
        : total > 0 && pct === 100
          ? "complete"
          : "in_progress";

  const alert: ProjectCardAlert | null = returnedTodo
    ? {
        kind: "returned",
        title: returnedTodo.requirement_description,
        authority: returnedTodo.approval_authority,
        waitingLabel: "returned for rework",
      }
    : submittedTodo
      ? {
          kind: "awaiting_approval",
          title: submittedTodo.requirement_description,
          authority: submittedTodo.approval_authority,
          waitingLabel: formatSlaTarget(submittedTodo.sla_target),
        }
      : null;

  const cells: ProjectCardCellState[] = todos.map((t) =>
    t.status === "complied"
      ? "complied"
      : t.approval_state === "returned"
        ? "returned"
        : t.approval_state === "submitted"
          ? "submitted"
          : "not_started",
  );

  const orderedSteps = steps.slice().sort((a, b) => a.ordering - b.ordering);
  const activeStep = orderedSteps.find((step) => {
    const stepTodos = todos.filter((t) => t.process_step_id === step.id);
    return stepTodos.length > 0 && stepTodos.some((t) => t.status !== "complied");
  });

  return {
    id: project.id,
    code: projectCode(project.id),
    name: project.name.trim() || "Untitled project (draft)",
    isDraft,
    status,
    pct,
    cells,
    stepLabel: activeStep ? activeStep.title : "All steps closed",
    alert,
  };
}

export const FILTER_KEYS = ["All", "Drafts", "Needs you", "With approvers", "In progress", "Complete"] as const;
export type ProjectFilterKey = (typeof FILTER_KEYS)[number];

export function matchesFilter(card: ProjectCardViewModel, filter: ProjectFilterKey): boolean {
  switch (filter) {
    case "All":
      return true;
    case "Drafts":
      return card.isDraft;
    case "Needs you":
      return card.status === "needs_action";
    case "With approvers":
      return card.status === "with_approver";
    case "In progress":
      return card.status === "in_progress";
    case "Complete":
      return card.status === "complete";
  }
}

export function matchesSearch(card: ProjectCardViewModel, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (card.name + " " + card.code).toLowerCase().includes(q);
}

export const SORT_OPTIONS = [
  { id: "status", label: "What needs me first" },
  { id: "progress", label: "Most progressed" },
  { id: "remaining", label: "Least progressed" },
  { id: "name", label: "Name A–Z" },
] as const;
export type ProjectSortKey = (typeof SORT_OPTIONS)[number]["id"];

const STATUS_RANK: Record<ProjectCardStatus, number> = {
  needs_action: 3,
  with_approver: 2,
  draft: 1,
  in_progress: 1,
  complete: 0,
};

export function sortCards(cards: ProjectCardViewModel[], sort: ProjectSortKey): ProjectCardViewModel[] {
  const copy = cards.slice();
  switch (sort) {
    case "progress":
      return copy.sort((a, b) => b.pct - a.pct);
    case "remaining":
      return copy.sort((a, b) => a.pct - b.pct);
    case "name":
      return copy.sort((a, b) => a.name.localeCompare(b.name));
    case "status":
    default:
      return copy.sort((a, b) => STATUS_RANK[b.status] - STATUS_RANK[a.status] || b.pct - a.pct);
  }
}

export interface DashboardStats {
  totalProjects: number;
  outForApproval: number;
  needsRework: number;
  fullyComplied: number;
}

export function computeStats(cards: ProjectCardViewModel[], allTodos: TodoItem[]): DashboardStats {
  return {
    totalProjects: cards.length,
    outForApproval: allTodos.filter((t) => t.approval_state === "submitted").length,
    needsRework: allTodos.filter((t) => t.approval_state === "returned").length,
    fullyComplied: cards.filter((c) => c.status === "complete").length,
  };
}

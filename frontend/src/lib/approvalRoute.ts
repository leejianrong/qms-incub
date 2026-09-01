// V11 (Q42): a static 3-node approval-route visualization (PM -> QA
// Office -> Authority) driven entirely by TodoItem.approval_state. There's
// no second role or gate yet (ADR-0002) — self-attestation moves a todo
// straight from not_started to approved, skipping "submitted" as a
// persisted state, but the view-model still renders it as a spot on the
// route in case a future reviewer flow pauses there.
import type { TodoItem } from "./api";

export type ApprovalNodeKey = "submitted" | "reviewed" | "approved";

export interface ApprovalNode {
  key: ApprovalNodeKey;
  label: string;
  highlighted: boolean;
}

export interface ApprovalRouteViewModel {
  nodes: ApprovalNode[];
  statusText: string;
  authority: string;
  slaText: string | null;
}

const NODE_LABELS: Record<ApprovalNodeKey, string> = {
  submitted: "Submitted",
  reviewed: "QA Office",
  approved: "Authority",
};

function highlightedNode(state: TodoItem["approval_state"]): ApprovalNodeKey | null {
  switch (state) {
    case "submitted":
      return "submitted";
    case "returned":
      return "reviewed";
    case "approved":
      return "approved";
    default:
      return null;
  }
}

function statusText(state: TodoItem["approval_state"]): string {
  switch (state) {
    case "not_required":
      return "Approval not required";
    case "not_started":
      return "Not yet submitted";
    case "submitted":
      return "Submitted, awaiting QA Office";
    case "returned":
      return "Returned — needs revision";
    case "approved":
      return "Approved";
  }
}

function slaText(slaTarget: string | null): string | null {
  if (!slaTarget) return null;
  const date = new Date(slaTarget);
  if (Number.isNaN(date.getTime())) return null;
  return `SLA: ${date.toLocaleDateString()}`;
}

export function approvalRouteViewModel(todo: TodoItem): ApprovalRouteViewModel {
  const active = highlightedNode(todo.approval_state);
  return {
    nodes: (["submitted", "reviewed", "approved"] as const).map((key) => ({
      key,
      label: NODE_LABELS[key],
      highlighted: key === active,
    })),
    statusText: statusText(todo.approval_state),
    authority: todo.approval_authority,
    slaText: slaText(todo.sla_target),
  };
}

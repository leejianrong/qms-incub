import { describe, expect, it } from "vitest";
import {
  buildProjectCard,
  computeStats,
  formatSlaTarget,
  matchesFilter,
  matchesSearch,
  projectCode,
  sortCards,
  type ProjectCardViewModel,
} from "./projectCards";
import type { Project, TodoItem, ProcessStep } from "./api";

function project(overrides: Partial<Project> = {}): Project {
  return {
    id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    name: "Ledger Recon",
    risk_tier: "high",
    aor_filename: null,
    aor_extracted_fields: null,
    ...overrides,
  };
}

function todo(overrides: Partial<TodoItem> = {}): TodoItem {
  return {
    id: "t1",
    project_id: "p1",
    requirement_id: "r1",
    requirement_description: "Document the data retention policy",
    clause_text: "clause",
    standard_name: "standard",
    status: "pending",
    process_step_id: "s1",
    approval_state: "not_required",
    approval_authority: "QA Office",
    sla_target: null,
    decided_at: null,
    ...overrides,
  };
}

const steps: ProcessStep[] = [
  { id: "s1", title: "Initiation", ordering: 0 },
  { id: "s2", title: "Design", ordering: 1 },
];

describe("projectCode", () => {
  it("derives a stable short code from a project id", () => {
    expect(projectCode("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")).toBe("PRJ-AAAAAA");
  });
});

describe("formatSlaTarget", () => {
  it("formats an ISO datetime as a short UTC target date", () => {
    expect(formatSlaTarget("2026-09-06T14:25:39.576274Z")).toBe("due Sep 6");
  });

  it("falls back to a placeholder when there's no target", () => {
    expect(formatSlaTarget(null)).toBe("just submitted");
  });

  it("falls back to a placeholder for an unparseable value", () => {
    expect(formatSlaTarget("not a date")).toBe("just submitted");
  });
});

describe("buildProjectCard", () => {
  it("is a draft when unclassified", () => {
    const card = buildProjectCard(project({ risk_tier: null }), [], steps);
    expect(card.isDraft).toBe(true);
    expect(card.status).toBe("draft");
    expect(card.pct).toBe(0);
  });

  it("flags needs_action and surfaces a rework alert when a todo was returned", () => {
    const todos = [todo({ approval_state: "returned", requirement_description: "Attach the DPIA" })];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.status).toBe("needs_action");
    expect(card.alert).toEqual({
      kind: "returned",
      title: "Attach the DPIA",
      authority: "QA Office",
      waitingLabel: "returned for rework",
    });
  });

  it("flags with_approver and surfaces an awaiting-approval alert when a todo is submitted", () => {
    const todos = [todo({ approval_state: "submitted", sla_target: "2026-09-06T14:25:39.576274Z" })];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.status).toBe("with_approver");
    expect(card.alert?.kind).toBe("awaiting_approval");
    expect(card.alert?.waitingLabel).toBe("due Sep 6");
  });

  it("returned takes priority over submitted when both are present", () => {
    const todos = [
      todo({ id: "t1", approval_state: "returned" }),
      todo({ id: "t2", approval_state: "submitted" }),
    ];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.status).toBe("needs_action");
    expect(card.alert?.kind).toBe("returned");
  });

  it("is complete when every todo is complied", () => {
    const todos = [todo({ status: "complied" }), todo({ id: "t2", status: "complied" })];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.status).toBe("complete");
    expect(card.pct).toBe(100);
    expect(card.alert).toBeNull();
  });

  it("is in_progress when some but not all todos are complied and none are submitted/returned", () => {
    const todos = [todo({ id: "t1", status: "complied" }), todo({ id: "t2", status: "pending" })];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.status).toBe("in_progress");
    expect(card.pct).toBe(50);
  });

  it("maps each todo to a progress cell colored by its state", () => {
    const todos = [
      todo({ id: "t1", status: "complied" }),
      todo({ id: "t2", approval_state: "submitted" }),
      todo({ id: "t3", approval_state: "returned" }),
      todo({ id: "t4" }),
    ];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.cells).toEqual(["complied", "submitted", "returned", "not_started"]);
  });

  it("picks the first ordered step with unfinished todos as the active step", () => {
    const todos = [
      todo({ id: "t1", process_step_id: "s1", status: "complied" }),
      todo({ id: "t2", process_step_id: "s2", status: "pending" }),
    ];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.stepLabel).toBe("Design");
  });

  it("reports all steps closed once every todo across every step is complied", () => {
    const todos = [
      todo({ id: "t1", process_step_id: "s1", status: "complied" }),
      todo({ id: "t2", process_step_id: "s2", status: "complied" }),
    ];
    const card = buildProjectCard(project(), todos, steps);
    expect(card.stepLabel).toBe("All steps closed");
  });

  it("falls back to a placeholder name for a blank project name", () => {
    const card = buildProjectCard(project({ name: "  " }), [], steps);
    expect(card.name).toBe("Untitled project (draft)");
  });
});

function card(overrides: Partial<ProjectCardViewModel> = {}): ProjectCardViewModel {
  return {
    id: "p1",
    code: "PRJ-000001",
    name: "Ledger Recon",
    isDraft: false,
    status: "in_progress",
    pct: 40,
    cells: [],
    stepLabel: "Design",
    alert: null,
    ...overrides,
  };
}

describe("matchesFilter", () => {
  it("All always matches", () => {
    expect(matchesFilter(card({ status: "complete" }), "All")).toBe(true);
  });

  it.each([
    ["Drafts", { isDraft: true }, true],
    ["Drafts", { isDraft: false }, false],
    ["Needs you", { status: "needs_action" as const }, true],
    ["Needs you", { status: "in_progress" as const }, false],
    ["With approvers", { status: "with_approver" as const }, true],
    ["In progress", { status: "in_progress" as const }, true],
    ["Complete", { status: "complete" as const }, true],
  ] as const)("%s filter", (filter, overrides, expected) => {
    expect(matchesFilter(card(overrides), filter)).toBe(expected);
  });
});

describe("matchesSearch", () => {
  it("matches on name case-insensitively", () => {
    expect(matchesSearch(card({ name: "Ledger Recon" }), "ledger")).toBe(true);
    expect(matchesSearch(card({ name: "Ledger Recon" }), "payroll")).toBe(false);
  });

  it("matches on code", () => {
    expect(matchesSearch(card({ code: "PRJ-ABCDEF" }), "abcdef")).toBe(true);
  });

  it("blank query matches everything", () => {
    expect(matchesSearch(card(), "  ")).toBe(true);
  });
});

describe("sortCards", () => {
  const cards = [
    card({ id: "a", name: "Zebra", status: "in_progress", pct: 30 }),
    card({ id: "b", name: "Alpha", status: "needs_action", pct: 10 }),
    card({ id: "c", name: "Mid", status: "complete", pct: 100 }),
  ];

  it("status: needs_action first, then by descending progress", () => {
    expect(sortCards(cards, "status").map((c) => c.id)).toEqual(["b", "a", "c"]);
  });

  it("progress: descending pct", () => {
    expect(sortCards(cards, "progress").map((c) => c.id)).toEqual(["c", "a", "b"]);
  });

  it("remaining: ascending pct", () => {
    expect(sortCards(cards, "remaining").map((c) => c.id)).toEqual(["b", "a", "c"]);
  });

  it("name: A-Z", () => {
    expect(sortCards(cards, "name").map((c) => c.id)).toEqual(["b", "c", "a"]);
  });

  it("does not mutate the input array", () => {
    const original = [...cards];
    sortCards(cards, "name");
    expect(cards).toEqual(original);
  });
});

describe("computeStats", () => {
  it("counts projects, out-for-approval, rework, and fully complied todos", () => {
    const cards = [card({ status: "complete" }), card({ status: "in_progress" })];
    const todos = [
      todo({ id: "t1", approval_state: "submitted" }),
      todo({ id: "t2", approval_state: "returned" }),
      todo({ id: "t3", approval_state: "not_required" }),
    ];
    expect(computeStats(cards, todos)).toEqual({
      totalProjects: 2,
      outForApproval: 1,
      needsRework: 1,
      fullyComplied: 1,
    });
  });
});

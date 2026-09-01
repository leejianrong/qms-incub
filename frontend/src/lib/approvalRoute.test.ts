import { describe, expect, it } from "vitest";
import { approvalRouteViewModel } from "./approvalRoute";
import type { TodoItem } from "./api";

function todo(overrides: Partial<TodoItem>): TodoItem {
  return {
    id: "t1",
    project_id: "p1",
    requirement_id: "r1",
    requirement_description: "desc",
    clause_text: "clause",
    standard_name: "standard",
    status: "pending",
    process_step_id: "initiation",
    approval_state: "not_started",
    approval_authority: "QA Office",
    sla_target: null,
    decided_at: null,
    ...overrides,
  };
}

describe("approvalRouteViewModel", () => {
  it("highlights no node and explains nothing is submitted for not_started", () => {
    const vm = approvalRouteViewModel(todo({ approval_state: "not_started" }));
    expect(vm.nodes.every((n) => !n.highlighted)).toBe(true);
    expect(vm.statusText).toBe("Not yet submitted");
  });

  it("highlights the Submitted node for submitted", () => {
    const vm = approvalRouteViewModel(todo({ approval_state: "submitted" }));
    expect(vm.nodes.find((n) => n.highlighted)?.key).toBe("submitted");
    expect(vm.statusText).toContain("awaiting QA Office");
  });

  it("highlights the QA Office node for returned", () => {
    const vm = approvalRouteViewModel(todo({ approval_state: "returned" }));
    expect(vm.nodes.find((n) => n.highlighted)?.key).toBe("reviewed");
    expect(vm.statusText).toContain("Returned");
  });

  it("highlights the Authority node for approved", () => {
    const vm = approvalRouteViewModel(todo({ approval_state: "approved" }));
    expect(vm.nodes.find((n) => n.highlighted)?.key).toBe("approved");
    expect(vm.statusText).toBe("Approved");
  });

  it("carries authority and formats the SLA date when present", () => {
    const vm = approvalRouteViewModel(
      todo({ approval_authority: "Chief Engineer", sla_target: "2026-09-10T00:00:00Z" }),
    );
    expect(vm.authority).toBe("Chief Engineer");
    expect(vm.slaText).toContain("SLA:");
  });

  it("omits SLA text when sla_target is null", () => {
    const vm = approvalRouteViewModel(todo({ sla_target: null }));
    expect(vm.slaText).toBeNull();
  });
});

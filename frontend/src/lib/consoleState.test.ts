import { describe, expect, it } from "vitest";
import { deriveUnseenPlanNotifications } from "./consoleState.svelte";
import type { Project } from "./api";

function project(overrides: Partial<Project>): Project {
  return {
    id: "p1",
    name: "Ledger Recon",
    risk_tier: null,
    aor_filename: null,
    aor_extracted_fields: null,
    ...overrides,
  };
}

describe("deriveUnseenPlanNotifications", () => {
  it("notifies for a classified project the viewer hasn't opened yet", () => {
    const projects = [project({ id: "p1", risk_tier: "high" })];
    const result = deriveUnseenPlanNotifications(projects, new Set());
    expect(result).toEqual([
      {
        id: "p1",
        title: "QMS plan ready — Ledger Recon",
        text: "Classification is complete and the todo list has been generated. Open the record to get started.",
      },
    ]);
  });

  it("skips a project that hasn't been classified yet", () => {
    const projects = [project({ id: "p1", risk_tier: null })];
    expect(deriveUnseenPlanNotifications(projects, new Set())).toEqual([]);
  });

  it("skips a classified project the viewer has already seen", () => {
    const projects = [project({ id: "p1", risk_tier: "low" })];
    expect(deriveUnseenPlanNotifications(projects, new Set(["p1"]))).toEqual([]);
  });

  it("falls back to a placeholder title for an unnamed project", () => {
    const projects = [project({ id: "p1", name: "  ", risk_tier: "medium" })];
    const result = deriveUnseenPlanNotifications(projects, new Set());
    expect(result[0].title).toBe("QMS plan ready — Untitled project");
  });
});

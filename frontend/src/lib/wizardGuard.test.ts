import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  cancelPendingNavigation,
  confirmPendingNavigation,
  getPendingNavigation,
  guardedNavigate,
  isWizardDirty,
  setWizardDirty,
} from "./wizardGuard.svelte";

beforeEach(() => {
  setWizardDirty(false);
  cancelPendingNavigation();
});

describe("wizardGuard", () => {
  it("navigates immediately when nothing is dirty", () => {
    const navigateImpl = vi.fn();
    guardedNavigate("/", navigateImpl);
    expect(navigateImpl).toHaveBeenCalledWith("/");
    expect(getPendingNavigation()).toBeNull();
  });

  it("holds the navigation instead of firing it while dirty", () => {
    setWizardDirty(true);
    const navigateImpl = vi.fn();
    guardedNavigate("/blog", navigateImpl);
    expect(navigateImpl).not.toHaveBeenCalled();
    expect(getPendingNavigation()).toBe("/blog");
  });

  it("cancelPendingNavigation clears the pending path without navigating", () => {
    setWizardDirty(true);
    guardedNavigate("/faq", vi.fn());
    cancelPendingNavigation();
    expect(getPendingNavigation()).toBeNull();
  });

  it("confirmPendingNavigation fires the held navigation and clears dirty", () => {
    setWizardDirty(true);
    guardedNavigate("/", vi.fn());
    const navigateImpl = vi.fn();
    confirmPendingNavigation(navigateImpl);
    expect(navigateImpl).toHaveBeenCalledWith("/");
    expect(getPendingNavigation()).toBeNull();
    expect(isWizardDirty()).toBe(false);
  });

  it("confirmPendingNavigation with nothing pending is a no-op", () => {
    const navigateImpl = vi.fn();
    confirmPendingNavigation(navigateImpl);
    expect(navigateImpl).not.toHaveBeenCalled();
  });
});

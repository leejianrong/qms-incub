// V13: a minimal client-side router for the console shell. Deliberately
// not a library (ADR-0013 only decided shadcn-svelte, not a router) — the
// core PM workflow is three views (dashboard/wizard/project detail), so a
// pathname string plus pushState/popstate is enough. Supersedes main.ts's
// "no router library yet" pathname-keyed mount for those three routes;
// QA-author tools (showcase/editor/content) and the standalone document
// upload utility keep the simple one-shot mount, since they're separate
// personas outside this slice's scope.

// Pure helpers, unit-tested independently of any window/history state.
export function pathOf(full: string): string {
  return full.split("?")[0];
}

export function paramOf(full: string, name: string): string | null {
  const qsIndex = full.indexOf("?");
  const qs = qsIndex >= 0 ? full.slice(qsIndex + 1) : "";
  return new URLSearchParams(qs).get(name);
}

function currentFull(): string {
  if (typeof window === "undefined") return "/";
  return window.location.pathname + window.location.search;
}

export const route = $state({ full: currentFull() });

export function navigate(path: string): void {
  if (path === route.full) return;
  if (typeof window !== "undefined") {
    window.history.pushState(null, "", path);
  }
  route.full = path;
}

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    route.full = currentFull();
  });
}

export function routePath(): string {
  return pathOf(route.full);
}

export function routeParam(name: string): string | null {
  return paramOf(route.full, name);
}

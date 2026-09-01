// V18 (Q53): client-only, non-persistent state backing the console shell's
// notification and favourites stubs. Nothing here is a real data model —
// it resets on reload by design. Real backend equivalents are tracked
// separately as GitHub issues #57 (todo comment threads), #58 (blog
// comments), #59 (notifications), #60 (favourites) on the QMS Incub board.
import { navigate } from "$lib/router.svelte";
import type { Project } from "$lib/api";

export interface ShellNotification {
  id: string;
  title: string;
  text: string;
}

// Pure and unit-testable: which classified (plan-ready) projects the
// viewer hasn't opened yet, in the shape the notification dropdown needs.
export function deriveUnseenPlanNotifications(
  projects: Project[],
  seenProjectIds: ReadonlySet<string>,
): ShellNotification[] {
  return projects
    .filter((project) => project.risk_tier !== null && !seenProjectIds.has(project.id))
    .map((project) => ({
      id: project.id,
      title: `QMS plan ready — ${project.name.trim() || "Untitled project"}`,
      text: "Classification is complete and the todo list has been generated. Open the record to get started.",
    }));
}

let seenProjectIds = $state<Record<string, true>>({});
let favoriteProjectIds = $state<Record<string, true>>({});
let favoritePostIds = $state<Record<string, true>>({});

export function getSeenProjectIds(): Record<string, true> {
  return seenProjectIds;
}

export function markProjectSeen(id: string): void {
  if (seenProjectIds[id]) return;
  seenProjectIds = { ...seenProjectIds, [id]: true };
}

export function markAllProjectsSeen(projects: Project[]): void {
  const next = { ...seenProjectIds };
  for (const project of projects) next[project.id] = true;
  seenProjectIds = next;
}

// Shared by every "open this project" affordance (dashboard cards, search
// results, the notification dropdown) so opening a project always clears
// its unread state, matching ui-reference/'s behavior.
export function goToProject(id: string): void {
  markProjectSeen(id);
  navigate(`/project?id=${id}`);
}

export function getFavoriteProjectIds(): Record<string, true> {
  return favoriteProjectIds;
}

export function isProjectFavorited(id: string): boolean {
  return !!favoriteProjectIds[id];
}

export function toggleFavoriteProject(id: string): void {
  const next = { ...favoriteProjectIds };
  if (next[id]) delete next[id];
  else next[id] = true;
  favoriteProjectIds = next;
}

export function getFavoritePostIds(): Record<string, true> {
  return favoritePostIds;
}

export function isPostFavorited(id: string): boolean {
  return !!favoritePostIds[id];
}

export function toggleFavoritePost(id: string): void {
  const next = { ...favoritePostIds };
  if (next[id]) delete next[id];
  else next[id] = true;
  favoritePostIds = next;
}

export function favoriteCount(): number {
  return Object.keys(favoriteProjectIds).length + Object.keys(favoritePostIds).length;
}

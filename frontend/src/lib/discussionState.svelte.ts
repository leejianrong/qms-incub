// V18 step 4 (Q53): client-only, non-persistent Discussion thread on a
// todo's detail panel — mirrors ui-reference/'s per-sub-step comments.
// No backend model exists for this; real work is tracked as GitHub issue
// #57 on the QMS Incub board. Comments reset on reload by design.
// Kept as its own module (like consoleState.svelte.ts) rather than local
// component state so a future cross-project "mentions" digest (the
// dashboard panel this slice deliberately left out, per
// ProjectsDashboard's PR) can read the same store without restructuring.
export interface DiscussionComment {
  who: string;
  role: string;
  text: string;
  postedAt: number;
}

let commentsByTodoId = $state<Record<string, DiscussionComment[]>>({});

export function getComments(todoId: string): DiscussionComment[] {
  return commentsByTodoId[todoId] ?? [];
}

export function postComment(todoId: string, who: string, role: string, text: string): void {
  const trimmed = text.trim();
  if (!trimmed) return;
  const existing = commentsByTodoId[todoId] ?? [];
  commentsByTodoId = {
    ...commentsByTodoId,
    [todoId]: [...existing, { who, role, text: trimmed, postedAt: Date.now() }],
  };
}

export function commentCount(todoId: string): number {
  return getComments(todoId).length;
}

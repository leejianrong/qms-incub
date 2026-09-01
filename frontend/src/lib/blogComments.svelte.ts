// V18 step 5 (Q53): client-only, non-persistent comments on a blog post's
// detail view — same pattern as discussionState.svelte.ts's todo Discussion
// thread, just keyed by blog post id instead of todo id. No backend model
// exists for this either; real work would be tracked the same way as
// discussionState.svelte.ts's issue #57 (a follow-up issue, not filed by
// this slice — see CLAUDE.md's "do not file GitHub issues" constraint).
// Comments reset on reload by design.
export interface BlogComment {
  who: string;
  role: string;
  text: string;
  postedAt: number;
}

let commentsByPostId = $state<Record<string, BlogComment[]>>({});

export function getComments(postId: string): BlogComment[] {
  return commentsByPostId[postId] ?? [];
}

export function postComment(postId: string, who: string, role: string, text: string): void {
  const trimmed = text.trim();
  if (!trimmed) return;
  const existing = commentsByPostId[postId] ?? [];
  commentsByPostId = {
    ...commentsByPostId,
    [postId]: [...existing, { who, role, text: trimmed, postedAt: Date.now() }],
  };
}

export function commentCount(postId: string): number {
  return getComments(postId).length;
}

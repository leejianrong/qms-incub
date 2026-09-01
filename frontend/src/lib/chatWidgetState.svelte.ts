// V18 step 7: client-only state backing the floating "Ask QMS Assistant"
// widget (mounted globally in Shell.svelte, replacing ProjectDetail.svelte's
// old inline chat card). The widget always calls the real V8 /chat endpoint
// (askChat in api.ts) — there is no fake "general" chat mode, because the
// backend's ChatRequest requires a project_id. This module owns the
// open/closed state, the draft, and the in-memory conversation log, plus
// the pure enabled/disabled decision the component renders from.
//
// Conversation history is non-persistent for the session (Q53, same
// treatment as discussionState.svelte.ts / consoleState.svelte.ts) — no
// backend model for chat history exists. The log resets whenever the open
// project id changes, mirroring ProjectDetail.svelte's old reset-on-
// project-id-change $effect.
import { askChat, type ChatAnswer, type Citation } from "$lib/api";

export interface ChatWidgetMessage {
  who: "user" | "assistant";
  text: string;
  citations: Citation[];
}

// Reference's aiPrompts (ui-reference/QMS Console.dc.html), kept as a
// reasonable adaptation — they just prefill the draft, no backend change.
export const QUICK_PROMPTS = [
  "What is blocking this project right now?",
  "Which approvals still need me?",
  "Summarise this step in plain English",
  "What usually gets this returned?",
];

// Pure: /chat has no "general" mode, so the widget can only ask a real
// question when a project is open.
export function isChatEnabled(projectId: string | null): boolean {
  return !!projectId;
}

export function chatInputPlaceholder(projectId: string | null): string {
  return isChatEnabled(projectId)
    ? "Ask about a step, an approval, or this project's state…"
    : "Open a project to ask about it";
}

let open = $state(false);
let draft = $state("");
let sending = $state(false);
let chatError = $state<string | null>(null);
let messages = $state<ChatWidgetMessage[]>([]);
let loggedProjectId = $state<string | null>(null);

export function isWidgetOpen(): boolean {
  return open;
}

export function toggleWidget(): void {
  open = !open;
}

export function closeWidget(): void {
  open = false;
}

export function getDraft(): string {
  return draft;
}

export function setDraft(text: string): void {
  draft = text;
}

export function isSending(): boolean {
  return sending;
}

export function getChatError(): string | null {
  return chatError;
}

export function getMessages(): ChatWidgetMessage[] {
  return messages;
}

// Call from a component $effect whenever the route's open project id
// changes. Starting a fresh conversation on a different project (or none)
// is fine per spec — this just decides when that reset should happen.
export function syncProject(projectId: string | null): void {
  if (projectId === loggedProjectId) return;
  loggedProjectId = projectId;
  messages = [];
  chatError = null;
  draft = "";
}

export async function sendWidgetMessage(
  apiBase: string,
  projectId: string,
  askChatImpl: typeof askChat = askChat,
): Promise<void> {
  const question = draft.trim();
  if (!question || sending || !projectId) return;
  sending = true;
  chatError = null;
  messages = [...messages, { who: "user", text: question, citations: [] }];
  draft = "";
  try {
    const result: ChatAnswer = await askChatImpl(apiBase, question, projectId);
    messages = [...messages, { who: "assistant", text: result.answer, citations: result.citations }];
  } catch (err) {
    chatError = err instanceof Error ? err.message : String(err);
  } finally {
    sending = false;
  }
}

// Test-only: lets discussionState-style tests get back to a clean slate
// between cases without reaching into module internals.
export function resetChatWidgetForTests(): void {
  open = false;
  draft = "";
  sending = false;
  chatError = null;
  messages = [];
  loggedProjectId = null;
}

<script lang="ts">
  // V18 step 7: floating "Ask QMS Assistant" widget, mounted once in
  // Shell.svelte so it's visible from every screen (ui-reference/'s
  // aiClosed/aiOpen launcher, adapted to our real project_id-scoped /chat
  // endpoint — no fake general-purpose mode, no file-attach since /chat
  // takes only question + project_id). Project-aware: functional when a
  // project route is open, disabled-but-visible otherwise.
  import SparklesIcon from "@lucide/svelte/icons/sparkles";
  import XIcon from "@lucide/svelte/icons/x";
  import SendIcon from "@lucide/svelte/icons/send";
  import { Button } from "$lib/components/ui/button/index.js";
  import { resolveApiBase } from "$lib/api";
  import { routeParam, routePath } from "$lib/router.svelte";
  import {
    QUICK_PROMPTS,
    chatInputPlaceholder,
    closeWidget,
    getChatError,
    getDraft,
    getMessages,
    isChatEnabled,
    isSending,
    isWidgetOpen,
    sendWidgetMessage,
    setDraft,
    syncProject,
    toggleWidget,
  } from "$lib/chatWidgetState.svelte";

  const apiBase = resolveApiBase(import.meta.env);

  // Same derivation ProjectDetail.svelte uses for its own project id: only
  // meaningful while the "/project" route is open, and reactive to it
  // changing (browser back/forward between projects, or leaving to another
  // screen entirely).
  const projectId = $derived(routePath() === "/project" ? routeParam("id") : null);

  $effect(() => {
    syncProject(projectId);
  });

  const enabled = $derived(isChatEnabled(projectId));

  function submit(event: Event) {
    event.preventDefault();
    if (!projectId) return;
    void sendWidgetMessage(apiBase, projectId);
  }
</script>

{#if !isWidgetOpen()}
  <button
    type="button"
    onclick={toggleWidget}
    class="fixed right-6 bottom-6 z-30 flex items-center gap-2.5 rounded-full bg-primary px-5 py-3 font-heading text-[13.5px] font-medium text-primary-foreground shadow-lg transition-colors hover:bg-primary/90"
  >
    <span class="flex size-[26px] flex-none items-center justify-center rounded-full bg-white/20">
      <SparklesIcon class="size-[15px]" />
    </span>
    <span>Ask QMS Assistant</span>
  </button>
{:else}
  <div
    class="fixed right-6 bottom-6 z-30 flex h-[min(620px,calc(100vh-96px))] w-[min(420px,calc(100vw-52px))] flex-col overflow-hidden rounded-2xl border border-border bg-background shadow-lg"
  >
    <div class="flex items-center gap-2.5 bg-primary px-4 py-3.5 text-primary-foreground">
      <span class="flex size-8 flex-none items-center justify-center rounded-full bg-white/20">
        <SparklesIcon class="size-[17px]" />
      </span>
      <div class="min-w-0">
        <div class="font-heading text-[15px] font-medium">QMS Assistant</div>
        <div class="text-[11px] opacity-85">
          {enabled ? "Reads the standard and this project's state" : "Open a project to ask about it"}
        </div>
      </div>
      <button
        type="button"
        onclick={closeWidget}
        aria-label="Close assistant"
        class="ml-auto flex size-7 flex-none items-center justify-center rounded-lg bg-white/20 transition-colors hover:bg-white/30"
      >
        <XIcon class="size-3.5" />
      </button>
    </div>

    <div class="flex-1 space-y-3 overflow-y-auto p-4">
      {#if !enabled}
        <p class="text-[13px] text-muted-foreground">
          Open a project to ask the assistant about it — answers are grounded in that project's todos and
          artifacts plus the policy corpus, so there's no general chat mode.
        </p>
      {:else if getMessages().length === 0}
        <p class="text-[13px] text-muted-foreground">
          Ask about this project's todos, approvals, or the underlying policy.
        </p>
      {/if}
      {#each getMessages() as message, i (i)}
        <div class={message.who === "assistant" ? "flex justify-start" : "flex justify-end"}>
          <div
            class={[
              "max-w-[88%] rounded-2xl px-3.5 py-2.5",
              message.who === "assistant"
                ? "rounded-bl-sm border border-border bg-muted"
                : "rounded-br-sm bg-primary text-primary-foreground",
            ]}
          >
            <div class="text-[9.5px] tracking-widest uppercase opacity-60">
              {message.who === "assistant" ? "QMS Assistant" : "You"}
            </div>
            <p class="mt-1.5 text-[13.5px] leading-relaxed">{message.text}</p>
            {#if message.citations.length > 0}
              <p class="mt-2 text-[11px] opacity-75">
                Policy sources: {message.citations.map((c) => c.document_title).join(", ")}
              </p>
            {/if}
          </div>
        </div>
      {/each}
      {#if getChatError()}
        <p class="text-[12.5px] text-destructive">Chat error: {getChatError()}</p>
      {/if}
    </div>

    <div class="border-t border-border bg-card p-3.5">
      {#if enabled}
        <div class="mb-2.5 grid grid-cols-2 gap-1.5">
          {#each QUICK_PROMPTS as prompt (prompt)}
            <button
              type="button"
              onclick={() => setDraft(prompt)}
              class="rounded-xl border border-border px-2.5 py-1.5 text-left text-[11.5px] leading-snug transition-colors hover:border-primary hover:text-primary"
            >
              {prompt}
            </button>
          {/each}
        </div>
      {/if}
      <form class="flex items-end gap-2" onsubmit={submit}>
        <textarea
          class="min-h-[54px] flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-60"
          value={getDraft()}
          oninput={(e) => setDraft((e.target as HTMLTextAreaElement).value)}
          placeholder={chatInputPlaceholder(projectId)}
          disabled={!enabled || isSending()}
        ></textarea>
        <Button
          type="submit"
          size="icon"
          class="flex-none"
          disabled={!enabled || isSending() || !getDraft().trim()}
          aria-label="Send"
        >
          <SendIcon class="size-4" />
        </Button>
      </form>
    </div>
  </div>
{/if}

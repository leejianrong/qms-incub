<script lang="ts">
  // V13 built the persistent shell as a bare header; V18 brings it to
  // visual/interaction parity with ui-reference/QMS Console.dc.html's
  // header — nav tabs with live counts, a favourites entry point, and a
  // notification bell backed by consoleState.svelte.ts's client-only
  // stub (Q53; real backend tracked as GitHub issue #59).
  import type { Snippet } from "svelte";
  import BellIcon from "@lucide/svelte/icons/bell";
  import StarIcon from "@lucide/svelte/icons/star";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import { navigate, routePath } from "$lib/router.svelte";
  import { resolveApiBase, listProjects, listBlogPosts, listFAQEntries, type Project } from "$lib/api";
  import { publishedPosts } from "$lib/blogCards";
  import { publishedFaqEntries } from "$lib/faqCards";
  import {
    deriveUnseenPlanNotifications,
    getSeenProjectIds,
    goToProject,
    markAllProjectsSeen,
    favoriteCount,
  } from "$lib/consoleState.svelte";
  import {
    guardedNavigate,
    getPendingNavigation,
    cancelPendingNavigation,
    confirmPendingNavigation,
  } from "$lib/wizardGuard.svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";

  let { children }: { children?: Snippet } = $props();

  const apiBase = resolveApiBase(import.meta.env);

  let projects = $state<Project[]>([]);
  let blogCount = $state(0);
  let faqCount = $state(0);
  let notifOpen = $state(false);

  async function load() {
    try {
      projects = await listProjects(apiBase);
    } catch {
      projects = [];
    }
    try {
      // Nav badge counts what the PM-facing Blog/FAQ views actually show
      // — published entries only (V6/ADR-0012's rule), not the admin's
      // full draft+published list — same publishedPosts/publishedFaqEntries
      // filter Blog.svelte/Faq.svelte apply.
      blogCount = publishedPosts(await listBlogPosts(apiBase)).length;
    } catch {
      blogCount = 0;
    }
    try {
      faqCount = publishedFaqEntries(await listFAQEntries(apiBase)).length;
    } catch {
      faqCount = 0;
    }
  }

  load();

  const notifications = $derived(deriveUnseenPlanNotifications(projects, new Set(Object.keys(getSeenProjectIds()))));
  const unreadCount = $derived(notifications.length);

  const navItems = $derived(
    [
      { key: "/", label: "Home", count: projects.length },
      { key: "/blog", label: "Blog", count: blogCount },
      { key: "/faq", label: "FAQ", count: faqCount },
    ].map((n) => ({ ...n, active: routePath() === n.key })),
  );

  function go(path: string) {
    notifOpen = false;
    guardedNavigate(path);
  }

  function openNotification(id: string) {
    notifOpen = false;
    goToProject(id);
  }

  function markAllRead() {
    markAllProjectsSeen(projects);
  }
</script>

<div class="min-h-screen bg-background text-foreground">
  <header
    class="sticky top-0 z-10 flex items-stretch gap-7 border-b border-border bg-card pr-6 shadow-sm"
  >
    <button
      type="button"
      onclick={() => go("/")}
      title="Back to home"
      class="flex flex-col justify-center gap-0.5 border-r border-border px-7 py-3 text-left transition-colors hover:bg-foreground/5"
    >
      <span class="font-heading text-base font-medium leading-tight whitespace-nowrap">
        Quality Management System
      </span>
      <span class="text-[11px] tracking-wide text-muted-foreground whitespace-nowrap">
        Software development · Rev. 4.2
      </span>
    </button>

    <nav class="flex items-stretch">
      {#each navItems as item (item.key)}
        <button
          type="button"
          onclick={() => go(item.key)}
          class={[
            "relative flex min-w-24 items-center justify-center gap-2 px-4 font-heading text-[13.5px] font-medium tracking-wide uppercase transition-colors hover:bg-foreground/5",
            item.active ? "text-foreground" : "text-muted-foreground",
          ]}
        >
          <span>{item.label}</span>
          <span class="text-[11px]" class:text-muted-foreground={!item.active}>{item.count}</span>
          {#if item.active}
            <span class="absolute inset-x-0 bottom-0 h-0.5 bg-primary"></span>
          {/if}
        </button>
      {/each}
    </nav>

    <div class="ml-auto flex items-center gap-3">
      <button
        type="button"
        onclick={() => go("/favourites")}
        title="Favourites"
        class={[
          "relative flex h-10 w-10 items-center justify-center rounded-xl transition-colors hover:bg-foreground/5",
          routePath() === "/favourites" ? "bg-accent text-primary" : "text-foreground",
        ]}
      >
        <StarIcon class="size-5" fill={favoriteCount() > 0 ? "currentColor" : "none"} />
        {#if favoriteCount() > 0}
          <span
            class="absolute top-1 right-0.5 flex h-[17px] min-w-[17px] items-center justify-center rounded-full border-2 border-card bg-foreground px-1 font-heading text-[10.5px] font-medium text-background"
          >
            {favoriteCount()}
          </span>
        {/if}
      </button>

      <div class="relative flex items-center">
        <button
          type="button"
          onclick={() => (notifOpen = !notifOpen)}
          title="Notifications"
          class={[
            "relative flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-foreground/5",
            notifOpen && "bg-foreground/5",
          ]}
        >
          <BellIcon class="size-5" />
          {#if unreadCount > 0}
            <span
              class="absolute top-1 right-0.5 flex h-[17px] min-w-[17px] items-center justify-center rounded-full border-2 border-card bg-destructive px-1 font-heading text-[10.5px] font-medium text-white"
            >
              {unreadCount}
            </span>
          {/if}
        </button>

        {#if notifOpen}
          <div
            class="absolute top-[52px] right-0 z-40 w-[380px] overflow-hidden rounded-2xl border border-border bg-card shadow-lg"
          >
            <div class="flex items-center gap-2.5 border-b border-border px-4 py-3.5">
              <span class="font-heading text-sm font-medium">Notifications</span>
              <span class="text-[11.5px] text-muted-foreground">
                {unreadCount > 0 ? `${unreadCount} unread` : "All read"}
              </span>
              <button
                type="button"
                onclick={markAllRead}
                class="ml-auto text-[11px] font-medium text-primary hover:underline"
              >
                Mark all read
              </button>
            </div>
            <div class="max-h-[340px] overflow-y-auto">
              {#each notifications as n (n.id)}
                <button
                  type="button"
                  onclick={() => openNotification(n.id)}
                  class="flex w-full items-start gap-3 border-b border-border bg-accent/40 px-4 py-3.5 text-left transition-colors hover:bg-foreground/5"
                >
                  <span class="mt-1.5 size-2 flex-none rounded-full bg-primary"></span>
                  <span class="min-w-0 flex-1">
                    <span class="block font-heading text-[13px] leading-tight font-medium">{n.title}</span>
                    <span class="mt-0.5 block text-xs leading-snug text-muted-foreground">{n.text}</span>
                  </span>
                </button>
              {:else}
                <div class="px-4 py-6 text-center text-[13px] text-muted-foreground">Nothing new right now.</div>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <div class="text-right text-[11px] leading-snug text-muted-foreground">
        <div class="font-heading text-[12.5px] font-medium text-foreground">Kim Alvarez</div>
        Project manager
      </div>
      <div
        class="flex size-9 flex-none items-center justify-center rounded-full bg-gradient-to-br from-[var(--color-accent-500)] to-[var(--color-accent-700)] font-heading text-[12.5px] font-medium text-white"
      >
        KA
      </div>
    </div>
  </header>

  <div>
    {@render children?.()}
  </div>

  <Dialog.Root
    open={getPendingNavigation() !== null}
    onOpenChange={(open) => {
      if (!open) cancelPendingNavigation();
    }}
  >
    <Dialog.Content>
      <Dialog.Header>
        <div class="flex items-center gap-3">
          <span class="flex size-[34px] flex-none items-center justify-center rounded-[10px] bg-destructive/10 text-destructive">
            <TriangleAlertIcon class="size-[18px]" />
          </span>
          <Dialog.Title>Discard project setup?</Dialog.Title>
        </div>
        <Dialog.Description>
          You have not generated the QMS plan yet. Leaving now discards the AOR upload and the clarification
          answers for this project.
        </Dialog.Description>
      </Dialog.Header>
      <Dialog.Footer>
        <Button variant="secondary" onclick={() => cancelPendingNavigation()}>Keep editing</Button>
        <Button onclick={() => confirmPendingNavigation(navigate)}>Discard and leave</Button>
      </Dialog.Footer>
    </Dialog.Content>
  </Dialog.Root>
</div>

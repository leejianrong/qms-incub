import { describe, expect, it, beforeEach, vi } from "vitest";
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
  resetChatWidgetForTests,
  sendWidgetMessage,
  setDraft,
  syncProject,
  toggleWidget,
} from "./chatWidgetState.svelte";
import type { ChatAnswer } from "./api";

beforeEach(() => {
  resetChatWidgetForTests();
});

describe("isChatEnabled / chatInputPlaceholder", () => {
  it("is disabled with no open project", () => {
    expect(isChatEnabled(null)).toBe(false);
    expect(chatInputPlaceholder(null)).toBe("Open a project to ask about it");
  });

  it("is enabled once a project id is present", () => {
    expect(isChatEnabled("p1")).toBe(true);
    expect(chatInputPlaceholder("p1")).not.toBe("Open a project to ask about it");
  });
});

describe("widget open/close", () => {
  it("starts closed and toggles", () => {
    expect(isWidgetOpen()).toBe(false);
    toggleWidget();
    expect(isWidgetOpen()).toBe(true);
    closeWidget();
    expect(isWidgetOpen()).toBe(false);
  });
});

describe("syncProject", () => {
  it("clears the log and draft when the open project id changes", () => {
    setDraft("hello");
    syncProject("p1");
    setDraft("draft for p1");
    syncProject("p2");
    expect(getDraft()).toBe("");
    expect(getMessages()).toEqual([]);
  });

  it("is a no-op when the project id is unchanged", () => {
    syncProject("p1");
    setDraft("keep me");
    syncProject("p1");
    expect(getDraft()).toBe("keep me");
  });
});

describe("sendWidgetMessage", () => {
  it("appends the user question then the assistant answer on success", async () => {
    setDraft("Am I compliant yet?");
    const askChatImpl = vi.fn(
      async (): Promise<ChatAnswer> => ({
        answer: "Not yet — two todos remain.",
        citations: [{ document_id: "d1", document_title: "Policy A" }],
      }),
    );
    await sendWidgetMessage("http://api", "p1", askChatImpl);

    expect(askChatImpl).toHaveBeenCalledWith("http://api", "Am I compliant yet?", "p1");
    expect(getDraft()).toBe("");
    expect(getMessages()).toEqual([
      { who: "user", text: "Am I compliant yet?", citations: [] },
      {
        who: "assistant",
        text: "Not yet — two todos remain.",
        citations: [{ document_id: "d1", document_title: "Policy A" }],
      },
    ]);
    expect(getChatError()).toBeNull();
    expect(isSending()).toBe(false);
  });

  it("records the error and keeps the user's question in the log on failure", async () => {
    setDraft("What is blocking this?");
    const askChatImpl = vi.fn(async (): Promise<ChatAnswer> => {
      throw new Error("backend returned 500");
    });
    await sendWidgetMessage("http://api", "p1", askChatImpl);

    expect(getMessages()).toEqual([{ who: "user", text: "What is blocking this?", citations: [] }]);
    expect(getChatError()).toBe("backend returned 500");
  });

  it("does nothing for a blank question", async () => {
    setDraft("   ");
    const askChatImpl = vi.fn();
    await sendWidgetMessage("http://api", "p1", askChatImpl);
    expect(askChatImpl).not.toHaveBeenCalled();
    expect(getMessages()).toEqual([]);
  });

  it("does nothing without an open project", async () => {
    setDraft("hello");
    const askChatImpl = vi.fn();
    await sendWidgetMessage("http://api", "", askChatImpl);
    expect(askChatImpl).not.toHaveBeenCalled();
  });
});

describe("QUICK_PROMPTS", () => {
  it("is a non-empty list of plain prefill strings", () => {
    expect(QUICK_PROMPTS.length).toBeGreaterThan(0);
    for (const prompt of QUICK_PROMPTS) expect(typeof prompt).toBe("string");
  });
});

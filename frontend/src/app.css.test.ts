import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function parseRootTokens(css: string): Record<string, string> {
  const rootBlock = css.match(/:root\s*\{([^}]*)\}/);
  if (!rootBlock) throw new Error("no :root block found");
  const tokens: Record<string, string> = {};
  for (const match of rootBlock[1].matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    tokens[match[1]] = match[2].trim();
  }
  return tokens;
}

// ui-reference/QMS Console.dc.html is the UI/UX engineer's design mock;
// its :root custom properties are the source of truth for these tokens
// (ADR-0013). app.css ports them verbatim.
const mockPath = resolve(import.meta.dirname, "../../ui-reference/QMS Console.dc.html");
const appCssPath = resolve(import.meta.dirname, "./app.css");

describe("design tokens ported from ui-reference", () => {
  const mockTokens = parseRootTokens(readFileSync(mockPath, "utf-8"));
  const appTokens = parseRootTokens(readFileSync(appCssPath, "utf-8"));

  const portedKeys = [
    "--color-shell",
    "--color-bg",
    "--color-surface",
    "--color-text",
    "--color-accent",
    "--color-accent-100",
    "--color-accent-300",
    "--color-accent-400",
    "--color-accent-500",
    "--color-accent-600",
    "--color-accent-700",
    "--color-accent-800",
    "--color-accent-900",
    "--color-error",
    "--color-error-bg",
    "--color-error-text",
    "--font-heading",
    "--font-body",
    "--radius-md",
    "--shadow-sm",
    "--shadow-md",
    "--shadow-lg",
  ];

  it.each(portedKeys)("%s matches ui-reference exactly", (key) => {
    expect(appTokens[key]).toBe(mockTokens[key]);
  });
});

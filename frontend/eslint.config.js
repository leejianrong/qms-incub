import js from "@eslint/js";
import svelte from "eslint-plugin-svelte";
import tseslint from "typescript-eslint";
import globals from "globals";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs["flat/recommended"],
  {
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    files: ["**/*.svelte"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },
  {
    // shadcn-svelte components are vendored, copied-into-repo source
    // (ADR-0013) — not hand-authored, so custom-element prop inference
    // (irrelevant here; this project compiles no custom elements) is
    // relaxed rather than reformatted to satisfy it.
    files: ["src/lib/components/ui/**/*.svelte"],
    rules: {
      "svelte/valid-compile": "off",
    },
  },
  {
    ignores: ["dist/", "node_modules/"],
  },
);

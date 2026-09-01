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
    // relaxed rather than reformatted to satisfy it. Same reasoning for
    // no-undef: this eslint-plugin-svelte/svelte-eslint-parser version
    // doesn't resolve Svelte 5 `generics="T = ..."` script-tag type
    // params (used by tooltip's Root/Trigger), a parser gap svelte-check
    // (which does understand it, see `npm run check`) already covers.
    files: ["src/lib/components/ui/**/*.svelte"],
    rules: {
      "svelte/valid-compile": "off",
      "no-undef": "off",
    },
  },
  {
    // Throwaway Playwright driver script used to screenshot-verify UI
    // changes (gitignored, never committed — see frontend/.gitignore).
    ignores: ["dist/", "node_modules/", "shot.local.mjs"],
  },
);

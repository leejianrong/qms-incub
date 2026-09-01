# ADR-0013: shadcn-svelte as the frontend component library

- Status: Accepted
- Date: 2026-09-01
- Deciders: leejianrong (user); agent

## Context

ADR-0009 decided the frontend stack (Svelte + Vite) but never picked a
component library — there was no need to yet, since the only UI built so
far is V1's single-input chat panel (`frontend/src/`, no Tailwind, no
component dependency beyond bare Svelte + hand-written CSS).

Replicating the `ui-reference/QMS Console.dc.html` design (a UI/UX
engineer's mock for the console frontend — dashboard, a multi-step project
wizard, a collapsible plan navigator, cards, tags, steppers, dropdowns,
modals) needs a broad, consistent set of primitives sharing one design
token system (the mock's purple/violet accent, Roboto, 10–16px radii,
soft shadows). Hand-rolling all of that — especially accessible dropdown/
modal/stepper behavior — is real, avoidable scope now that the frontend is
about to grow past one chat panel.

## Decision

Adopt **shadcn-svelte** as the frontend component library. Components are
copied into `frontend/src/lib/components/ui/` (its standard model), not
pulled in as an opaque npm dependency, and themed via CSS custom
properties matching `ui-reference/`'s tokens (accent color, radius,
shadows) instead of shadcn's own defaults.

This brings two things into the frontend toolchain that aren't there
today: **Tailwind CSS** (shadcn-svelte's styling model) and **Bits UI**
(the headless/accessible primitives shadcn-svelte wraps for dialog,
dropdown, popover, etc.). Both are additions on top of ADR-0009's stack,
not a reversal of it.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Skeleton UI | Svelte-native, but no copy-into-repo model — theming fights its own defaults rather than starting from `ui-reference/`'s tokens |
| A Material-for-Svelte library (e.g. svelte-materialify) | `ui-reference/` explicitly re-skins Material tokens toward a custom purple/violet brand (red reserved for errors only); adopting an actual Material library works against that rather than for it |
| Hand-rolled components matching the mock 1:1 | Highest fidelity, but reimplements accessible dropdown/dialog/stepper behavior that's already solved, for every future screen this console needs |

## Consequences

Gains: consistent, accessible primitives (dialog, dropdown, popover,
select) without hand-rolling ARIA behavior; the copy-into-repo model keeps
the dependency footprint inspectable and easy to theme against
`ui-reference/`'s tokens rather than fighting a black-box library's
defaults.

Costs: Tailwind CSS and its Vite plugin enter the frontend build for the
first time — a new toolchain piece, not just a new npm package. Bits UI
becomes a new runtime dependency. Existing hand-written CSS in
`frontend/src/app.css` and any future components need to coexist with
Tailwind's utility classes rather than being replaced wholesale in one
pass.

Forecloses: nothing structural — shadcn-svelte components are copied
source, not a locked-in framework dependency; swapping the underlying
primitive library later touches the copied component files, not app code
that consumes them.

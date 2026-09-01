# agent-skills

Two Claude Code **agent skills** that turn a software project's engineering
evidence into auditable QMS lifecycle documentation.

> **First cut.** This is our first attempt at using agents to generate
> QMS-compliance documentation, and it should be read as an experiment rather
> than an established process. The intent is to learn what agents can and
> cannot credibly produce from engineering evidence — expect the skills, the
> document shapes and the workflow around them to change as we find out, and
> to improve as we do (see *Where this is heading*). Treat
> every output as a draft for human review (that constraint is built into the
> skills themselves, see *The assistant is not the authority* below), and
> please feed back where the output was wrong, thin, or asked for the wrong
> things.

**Primary audience: the Product Manager.** These skills exist so a PM can
assemble the compliance paperwork for a phase gate without hand-writing it from
scratch, and can see at a glance where the project's evidence is genuinely
incomplete. You do not need to read code to use them — you do need to review
what comes out. Developers maintaining or extending the skills should read
*For developers* at the bottom.

Both are **project-agnostic** — they resolve the target project from your
request or the working directory, and hard-code no project name, requirement
ID, path or repository. Neither is specific to `qms-incub`; you can point them
at any repo.

| Skill | Lifecycle phase | Produces |
|---|---|---|
| `system-design-qms` | System Design — runs **before** DTE | SDD, SwRS, SwDD, RTM, design findings, design readiness summary |
| `dte-qms` | Development, Test & Evaluation — runs **after** design review | Acceptance Test Procedure, Functional Test Results, Unit Test Results |

```
VERIFIED REQUIREMENTS
        ↓
  system-design-qms  →  SDD · SwRS · SwDD · RTM
        ↓
  HUMAN DESIGN REVIEW  →  APPROVED DESIGN BASELINE
        ↓
  DEVELOPMENT
        ↓
  dte-qms  →  ATP · Functional Test Results · Unit Test Results
```

## The shared contract

Everything else follows from three rules, and they are the point of these
skills — not the document templates.

**1. Evidence only.** Every claim in every generated document must be supported
by evidence actually retrieved during that run. Never fabricated:
requirements · implementation · tests · issue numbers · PRs · commit SHAs ·
CI runs · CI results · coverage · test results · artifacts · approvals ·
dates · personnel · signatures. An honest gap is a correct result; a
plausible-looking invention is a defect that can propagate into a real quality
record.

**2. "Absent" and "couldn't look" are different findings.** This is the single
most important correctness property. `dte-qms` uses four evidence states:

- `Evidence exists` — you read it, and can cite it
- `Evidence does not exist` — you could query the source, and the item is genuinely absent
- `Evidence could not be retrieved` — you could not query the source (no access, no integration, tool unavailable)
- `Evidence is ambiguous` — you found something, and it doesn't settle the question

Conflating the middle two turns a tooling limitation into a false finding
against the project. `system-design-qms` uses a parallel label set for
requirements authority: `VERIFIED` · `EVIDENCE` · `DERIVED` · `PROPOSED` ·
`MISSING` · `CONFLICTING` · `HUMAN REVIEW REQUIRED`.

**3. The assistant is not the authority.** The skill finds evidence, analyses
it, identifies gaps, proposes design, generates documents, maintains
traceability. The responsible engineer / PM / customer / safety authority
reviews, endorses, approves, baselines. Every generated document is **DRAFT**
until a human approves it. In particular the skills will not declare a safety
control adequate, will not report a test as passing without an execution
record, and will not infer CI success from the existence of a workflow file.

A corollary worth knowing before you run either one: **a gap is a finding to be
recorded, not a defect to be fixed.** Neither skill will add code, tests,
requirements or issues to make traceability look complete. Remediation is a
separate task you have to ask for explicitly.

## What gets written

Both skills write **only** under `<target-project>/output/` and never modify the
target project's source, tests, requirements or configuration.

```
<target-project>/output/
  # system-design-qms
  system-design-document.md
  software-requirements-specification.md
  software-design-document.md
  requirements-traceability-matrix.md
  system-design-findings.md
  design-readiness-summary.md
  # dte-qms
  acceptance-test-procedure.md
  functional-test-results.md
  unit-test-results.md
```

The RTM is the hinge artefact: `system-design-qms` builds it
(System Requirement → Software Requirement → Design Element → Implementation →
Test) and `dte-qms` extends the verification end of the same chain
(Requirement → Issue/Change → Implementation → Test → CI Execution → Result).

## Where this is heading

The skills will keep improving, and the document shapes above are the part most
likely to change.

The clearest next step: **feed in real approved documents and derive proper
templates from them.** The section outlines currently baked into the skills are
a reasonable first guess at a QMS document, not your organisation's controlled
template. Once we have approved documents to work from, a developer can turn
them into templates the skills generate against — correct section structure,
correct field names, correct terminology, matching what a reviewer actually
expects to see. That should cut review effort considerably, because the output
stops being "a document about the right things" and starts being the document
in the shape it's meant to be in.

Two constraints that will not be relaxed as this evolves, because they're the
reason the output is trustworthy at all:

- An approved document supplied as input is **evidence and a template source**.
  It never licenses the skill to describe its own output as approved.
- A template makes the output better shaped, not better supported. Every field
  still needs real evidence behind it, and an empty field stays explicitly
  empty rather than being filled to complete the template.

Other directions under consideration: broader lifecycle coverage beyond these
two phases, richer CI/CD execution evidence where the integrations allow it,
and reusing an RTM across runs instead of rebuilding it. Nothing here is
committed — feedback from real use decides the order.

---

## For the Product Manager

You are the intended user of these skills, and the reviewer of everything they
produce. The short version of your job here: **point the skill at the right
evidence, then read the output as a draft you own.** The skill does the
assembling and the gap-hunting; the judgement about whether a gap matters, and
whether the document is fit to become a quality record, stays with you and the
responsible engineer.

Practical expectations for a first-cut run:

- It will not fill in what it cannot find. A run that comes back with a page of
  `MISSING` and `Evidence could not be retrieved` rows has told you something
  real about the project's evidence, and is working as designed.
- It will not tidy the project to make the paperwork look better. If a
  requirement has no test, you get a finding, not a new test.
- It cannot approve anything. No sign-off blocks, no reviewer names, no
  document control numbers unless those came from real evidence — precisely so
  a draft can't be mistaken for an approved record.
- Nothing it writes is authoritative until you route it through your actual
  review and approval.

If you hit something you can't act on — an artefact you needed that wasn't
generated, a finding you can't interpret, a document that asked for input you
don't have — that's a gap in this first cut, not a mistake on your part. Raise
it.

### Installing

A one-time setup step. If you'd rather not run shell commands, ask a developer
to do this once for your machine — after that, invoking the skills is just
typing in Claude Code.

Skills are directories containing a `SKILL.md` with YAML frontmatter
(`name`, `description`). Claude Code discovers them from two places:

| Location | Scope |
|---|---|
| `~/.claude/skills/<name>/SKILL.md` | Personal — available in every project on your machine |
| `<repo>/.claude/skills/<name>/SKILL.md` | Project — committed, so everyone on the repo gets it |

To install these personally:

```bash
mkdir -p ~/.claude/skills
cp -r agent-skills/dte-qms agent-skills/system-design-qms ~/.claude/skills/
```

Prefer symlinks while you're still editing them, so the installed copy can't
drift from the repo copy:

```bash
ln -sfn "$PWD/agent-skills/dte-qms"           ~/.claude/skills/dte-qms
ln -sfn "$PWD/agent-skills/system-design-qms" ~/.claude/skills/system-design-qms
```

Restart Claude Code (or start a new session) after installing. Run `/skills` to
confirm both appear.

### Invoking

Three ways, all equivalent in effect:

- **Slash command** — `/system-design-qms` or `/dte-qms`, optionally with args:
  `/dte-qms audit traceability for ../hello-project`
- **Natural language** — the `description:` in each `SKILL.md` is what Claude
  matches against, so asking for the artefact by name is enough: "produce an
  Acceptance Test Procedure for this repo", "generate an SDD and RTM from
  `docs/requirements.md`", "audit this repo's requirement-to-verification
  traceability".
- **Delegated to a subagent** — useful for a long evidence sweep you don't want
  filling your main context.

### Giving it what it needs

`system-design-qms` **requires** two things and will stop rather than guess:

1. a **verified** System Requirements Specification (say where it is, and that
   it's the authoritative baseline)
2. a project/repository holding the engineering evidence

If you can't supply a baseline, that's itself a design readiness issue and the
skill reports it as one instead of inventing a baseline.

Optional inputs it will use if you point at them: existing SDD/SwRS/SwDD/RTM,
architecture docs, interface specs, customer or contractual requirements,
applicable standards, QMS procedures, safety classification, hazard analysis
and hazard log, safety and security requirements, an existing Acceptance Test
Plan, constraints, assumptions, design decisions, risk register, GitHub Issues
and PRs, Git history, source, tests, CI config and results.

`dte-qms` works from whatever is discoverable, but access matters: if a GitHub
integration is configured it can cite real issue/PR numbers and check runs;
without one, those rows come back `Evidence could not be retrieved` rather than
as gaps.

### Reading the output

Read the **Limitations** and **status summary** sections first. A run that
reports "no execution evidence was retrieved" is a successful run, not a broken
one — it tells you what the record does not know. Then check that nothing you
care about is marked `Fully Traced` on the strength of a test file existing;
the skills are instructed not to do that, and it's the thing worth
spot-checking.

Everything is DRAFT. Route it through your actual review and approval before it
becomes a quality record.

---

## For developers

### Editing a skill

A skill is just Markdown — the frontmatter `description` is the routing signal
(it's what Claude sees when deciding whether the skill is relevant), and the
body is the instructions injected into the turn. So:

- Keep `description` written as **trigger conditions plus a refusal boundary**.
  Both current descriptions name the artefacts by their real-world names
  ("Acceptance Test Procedure", "Requirements Traceability Matrix") and end
  with what the skill will not do. That phrasing is doing the work of getting
  the skill picked up at the right moment and not at the wrong one.
- Keep the body **imperative and ordered**. Both skills gate document
  generation behind completed analysis steps (`dte-qms` steps 1–11 before 12;
  `system-design-qms` steps 1–5 before 6) and close with an explicit
  self-check pass. That structure is load-bearing — it's what stops the model
  jumping to a nice-looking template.
- **Don't reintroduce project specifics.** No project name, requirement ID,
  path, issue number or repo in the skill body. Discovery hints (`tests/`,
  `.github/workflows/`, `src/`) are fine — they're described as starting
  points, not a fixed layout.
- When you add a rule, say **why** it exists. The existing rules earn
  compliance by explaining the failure they prevent ("conflating them turns a
  tooling limitation into a false finding against the project"), not by
  shouting.

### Testing a change

There is no test harness for skills; the honest loop is behavioural:

1. Restart the session so the edited `SKILL.md` is reloaded.
2. Run the skill against a small throwaway project with **known** evidence
   gaps — one requirement with no test, one test with no execution record, no
   configured GitHub integration.
3. Grade the output against the skill's own final-check list. The failures
   worth hunting: a gap silently repaired, `Evidence could not be retrieved`
   downgraded to `Evidence does not exist`, a pass reported from a test file's
   existence, CI success inferred from `ci.yml`, an invented issue number or
   commit SHA, a signature or reviewer block with a plausible name in it.
4. Confirm nothing outside `<target-project>/output/` was written
   (`git status` in the target).

### Repo status, and the drift you should know about

`agent-skills/` is currently **untracked** in this repo, and the copies in
`~/.claude/skills/` are byte-identical copies rather than symlinks — so they
can silently diverge. Two things worth doing:

- Commit `agent-skills/` so the skills are versioned and reviewable like the
  rest of the repo.
- Either symlink into `~/.claude/skills/` (see above) or move the canonical
  copy to `.claude/skills/` so the whole team gets it from a checkout with no
  install step. This repo already has the precedent for the symlink approach in
  `make install-hooks`, which symlinks `scripts/git-hooks/pre-push` into
  `.git/hooks/`.

Note that these skills are documentation-generation tooling *about* projects —
they are not part of the `qms-incub` product surface, which per ADR-0012 is
ingestion-and-chat only and never authors document content. Keep that boundary:
nothing in the backend should call or depend on these.

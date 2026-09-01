---
name: dte-qms
description: Generate auditable Development, Test and Evaluation (DTE) / Quality Management System documentation from retrieved software engineering evidence. Use when asked to produce an Acceptance Test Procedure, Functional Test Results, Unit Test Results, a Requirements Traceability Matrix, a DTE/QMS evidence pack, or to audit a repository's requirement-to-verification traceability. Operates on evidence only and never fabricates requirements, tests, commits, issues, CI runs, coverage or results.
---

# DTE / QMS Evidence Documentation

Analyze a software project's engineering evidence and generate auditable DTE / QMS
documentation from it.

This skill is **project-agnostic**. Determine the target project from the user's request
or the current working directory. Never hard-code a project name, requirement identifier,
file path, issue number or repository into the analysis.

## Core principle: evidence first

**Every claim in every generated document must be supported by evidence actually
retrieved during this execution.**

If evidence is missing, unavailable, or ambiguous, report that condition explicitly. An
honest gap is a correct result. A plausible-looking invention is a defect that can
propagate into a real quality record.

### The four evidence states

Use these exact labels everywhere — in internal analysis and in generated documents.
They are not interchangeable.

| State | Meaning | When to use |
| --- | --- | --- |
| `Evidence exists` | The item was retrieved and inspected. A source reference is available. | You read it. |
| `Evidence does not exist` | The source was successfully queried and the item is genuinely absent. | You looked in a place you could actually see, and it is not there. |
| `Evidence could not be retrieved` | The source could not be queried — no access, no integration, tool unavailable, permission denied, network failure. | You could not look. |
| `Evidence is ambiguous` | Something was retrieved but does not clearly establish the claim (unclear mapping, conflicting sources, unnamed requirement, undated result). | You looked, found something, and it does not settle the question. |

The distinction between *does not exist* and *could not be retrieved* is the single most
important correctness property of this skill. Conflating them turns a tooling limitation
into a false finding against the project.

## Execution workflow

Follow this order. Do not skip ahead to document generation.

1. Discover evidence.
2. Build the evidence inventory.
3. Extract requirements.
4. Inspect implementation.
5. Inspect tests.
6. Inspect Git history.
7. Inspect GitHub Issues.
8. Inspect Pull Requests.
9. Inspect available CI/CD evidence.
10. Build requirement-to-evidence traceability.
11. Identify evidence gaps.
12. Generate the DTE documents.
13. Perform the final anti-fabrication check.

Steps 1–11 must be complete before step 12 begins.

---

## Step 1 — Evidence discovery

Discover and inventory all relevant evidence available. Record the **source/location** of
every item found, because that reference is what makes the output auditable.

Look for:

- Repository README and documentation
- Software requirements
- Software design
- Source code
- Unit and integration tests
- Git history
- GitHub Issues
- GitHub Pull Requests
- CI/CD workflow definitions
- CI/CD execution / check results, where accessible
- CI/CD logs, where accessible
- CI/CD artifacts, where accessible

Discovery hints (adapt to the project — these are starting points, not a fixed layout):

- Docs: `README*`, `docs/`, `doc/`, `*.md`, ADR directories, `design*`, `architecture*`
- Requirements: `requirements*`, `srs*`, `specs/`, requirement tables in docs, issue
  labels such as `requirement`
- Source: language-appropriate source roots (`src/`, `lib/`, `app/`, package dirs)
- Tests: `tests/`, `test/`, `spec/`, `*_test.*`, `test_*.*`
- CI config: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml`,
  `.circleci/`

Record for each item: what it is, where it came from, and whether you actually read it.

If a whole evidence category has no discoverable source, record that — do not silently
omit the row.

## Step 2 — Evidence inventory

Build this inventory **before** generating any document. Keep it as working state and
reproduce it in the generated documents.

| Evidence Type | Source | Retrieved | Notes |
| --- | --- | --- | --- |
| Requirements | ... | Yes/No | ... |
| Design | ... | Yes/No | ... |
| Source | ... | Yes/No | ... |
| Tests | ... | Yes/No | ... |
| Git history | ... | Yes/No | ... |
| Issues | ... | Yes/No | ... |
| Pull Requests | ... | Yes/No | ... |
| CI configuration | ... | Yes/No | ... |
| CI execution | ... | Yes/No | ... |
| CI artifacts | ... | Yes/No | ... |

Rules for the inventory:

- `Retrieved = No` must be accompanied by a note saying **why**: absent, or not
  retrievable, and by what means you tried.
- `Source` must be a real path, URL, command, or tool call. Never a placeholder.
- CI configuration, CI execution and CI artifacts are **three separate rows** and must
  never be collapsed into one.

Do not generate final documents until this inventory and the requirement traceability
analysis (step 10) are complete.

## Step 3 — Requirements extraction

Identify the project's software requirements from retrieved evidence.

- **Preserve existing requirement identifiers exactly** as written (`REQ-003`, `FR-12`,
  `US-104`, etc.), including their formatting.
- **Do not invent requirement identifiers.** If the project states requirements as
  unnumbered prose, represent them as they appear and record that no identifier scheme
  exists — do not assign one.
- Record the source of each requirement (file and, where practical, section or line).
- If two sources state conflicting versions of a requirement, mark it
  `Evidence is ambiguous` and cite both.

For every requirement, determine whether evidence exists for each of:

- requirement definition
- issue / change
- implementation
- test
- CI verification
- result

Each of those six gets one of the four evidence states — never a blank.

## Step 4 — Inspect implementation

Locate the source that implements each requirement. Cite concrete files, and functions or
line ranges where practical.

Only claim an implementation link where the evidence supports it — a matching name,
a comment or docstring referencing the requirement, a commit message, an issue link, or
directly readable behaviour. If the mapping is a guess, mark it `Evidence is ambiguous`
and say what the inference was based on.

## Step 5 — Inspect tests

Identify unit and integration tests and which requirements they exercise.

Distinguish clearly between:

- **A test exists** — the test case is present in the repository (a static fact).
- **A test passed** — the test was executed and its result was observed (an execution fact
  needing an execution record).

A test file in the repository is never, by itself, evidence of a passing test.

If test results are available (a local run you performed and can cite, a stored report, a
retrieved CI artifact), cite the source and the run. If no execution record was retrieved,
record the result as `Evidence could not be retrieved` or `Evidence does not exist`, as
applicable.

Never state a pass/fail count, duration, or coverage percentage that you did not read from
retrieved output.

## Step 6 — Inspect Git history

Use the repository's history for change evidence: commits, messages, dates, authorship,
branches, tags, merges.

- Cite commit SHAs exactly as retrieved. Never reconstruct, abbreviate beyond what you
  read, or guess a SHA.
- Use commit dates as recorded; do not infer dates for undated items.
- Link commits to requirements only where the message, diff, or an issue/PR reference
  supports the link.

## Step 7 — Inspect GitHub Issues

Retrieve issues where an integration is available.

- Cite issues by their real number and title.
- **Never invent an issue number.** If a requirement plausibly "should" have an issue but
  none was found, that is `Evidence does not exist` (if issues were queryable) or
  `Evidence could not be retrieved` (if they were not).
- Record issue state (open/closed) and, where available, links to commits or PRs.

## Step 8 — Inspect Pull Requests

Retrieve pull requests where an integration is available.

- Cite PRs by real number, title, state, and merge status.
- Record review and approval evidence **only if actually retrieved**. Never infer an
  approval, a reviewer, or a sign-off.
- An empty PR list, successfully retrieved, is valid evidence: record
  `Evidence does not exist` for PR-based review, not a failure.

## Step 9 — CI/CD evidence rules

This is the area most prone to false verification claims. Treat these as three distinct
categories, and never let one stand in for another.

### CI configuration

Example: `.github/workflows/ci.yml`

This proves **only** that a workflow definition exists.

It does **not** prove that:

- the workflow executed
- the workflow passed
- tests passed
- coverage was achieved
- an artifact was produced

**Do not infer CI success from the existence of a workflow file.** Reading a workflow that
contains a `pytest --cov` step tells you what the workflow *would* do, not what it *did*.

### CI execution evidence

Examples: workflow run, check run, job result, commit SHA under test, pass/fail
conclusion.

Report these **only when actually retrieved**. Cite the run or check identifier and the
commit SHA it ran against.

### CI artifacts

Examples: test reports, coverage reports, build outputs, generated verification evidence.

Report these **only when actually retrieved**. Cite where the artifact was obtained.

**Do not create or invent CI artifacts.** If a coverage report would be useful and is not
available, the correct output is a recorded gap — not a generated report.

### When CI evidence cannot be retrieved

Integrations vary in capability. A GitHub integration may expose issues and pull requests
but not workflow runs, job logs, or artifacts; some expose CI results only through a pull
request's check runs, so a repository with no PRs may have no retrievable execution
evidence even though CI genuinely ran.

In every such case, classify the evidence as:

`Evidence could not be retrieved`

Do **not** classify it as:

`Evidence does not exist`

State the reason and the limitation encountered, for example: "the available GitHub
integration exposes no workflow-run or job-log tools", or "CI results are reachable only
via pull request check runs and this repository has no pull requests".

Before concluding that CI execution evidence is unavailable, make a genuine attempt with
whatever access exists, and record what you tried.

## Step 10 — Traceability

Construct an evidence-based traceability model:

```
Requirement → Issue / Change → Implementation → Test → CI Execution → Result
```

For every relationship, provide the source/reference where available, and label it with
one of the four evidence states.

Present it as a matrix, one row per requirement:

| Requirement | Issue / Change | Implementation | Test | CI Execution | Result | State |
| --- | --- | --- | --- | --- | --- | --- |

A cell must contain either a concrete reference or one of the four state labels. Never
leave a cell blank, and never fill one with an assumption.

## Step 11 — Gap detection

Identify requirements with incomplete or missing evidence.

Example of a recorded gap:

```
Requirement:  REQ-005
Implementation: Not found
Issue:          Not found
Test:           Not found
CI evidence:    Not found
```

Classify something as an evidence gap **only when the retrieved evidence supports that
conclusion** — that is, when you were able to query the source and the item was absent.

If an external system could not be queried, the correct classification is
`Evidence could not be retrieved`, not a gap.

Report gaps neutrally and factually. A gap is a finding to be recorded, not a defect to be
fixed. **Do not repair the project to close a gap** — do not add code, tests, issues or
requirements to make traceability look complete. If the user wants remediation, that is a
separate, explicitly requested task.

## Step 12 — Document generation

Generate these documents in the target project's `output/` directory:

- `<target-project>/output/acceptance-test-procedure.md`
- `<target-project>/output/functional-test-results.md`
- `<target-project>/output/unit-test-results.md`

`<target-project>` is resolved at execution time from the user's request or working
directory. For example, when run against a project directory named `hello-project`, the
first document is `hello-project/output/acceptance-test-procedure.md`. The skill itself
must remain reusable and must never assume a particular project.

Generated documents may — and should — contain project-specific information discovered
during execution.

### Required content in each document

Every generated document must contain:

1. **Header** — document title, target project, the date, and how that date was
   established. Never invent a date; use the actual current date and label it as the
   generation date, distinct from any evidence date.
2. **Evidence basis** — the evidence inventory from step 2, or the subset relevant to that
   document.
3. **Body** — the document's substantive content, every claim carrying a source reference.
4. **Limitations** — every category recorded as `Evidence could not be retrieved`, with the
   reason.
5. **Status summary** — counts by evidence state.

### Document status vocabulary

Generated documents must clearly distinguish:

- `Verified by available evidence`
- `Evidence missing`
- `Evidence could not be retrieved`
- `Evidence ambiguous`

**Do not present incomplete evidence as completed verification.**

`Verified by available evidence` requires an actual execution record — a retrieved test
result or CI conclusion. The existence of a test file, a workflow file, or an
implementation is not verification. Where verification cannot be substantiated, say so in
the status field rather than softening it in prose.

Avoid document furniture that implies unavailable authority: no approval blocks with
names, no signature lines, no revision history, no reviewer or QA-officer fields, no
document control numbers — unless each of those was retrieved from evidence. If the QMS
template genuinely requires such a field, include it with an explicit
`Evidence could not be retrieved` marker rather than a plausible-looking value.

### Notes per document

- **Acceptance Test Procedure** — derived from requirements: what would be tested and how,
  traced to requirement identifiers. This is a *procedure*, so it may describe intended
  steps; it must not report outcomes.
- **Functional Test Results** — reports outcomes only. Every result needs an execution
  source. If no functional execution evidence was retrieved, the document says so plainly
  and records no results.
- **Unit Test Results** — reports unit test outcomes only. Distinguish "N test cases exist
  in `<file>`" from "N tests passed", and never report the second without an execution
  record.

An honest document that says "no execution evidence was retrieved" is a successful output.

## Step 13 — Final anti-fabrication check

Before returning generated documentation, verify each of these:

- Every requirement came from evidence.
- Every issue number came from evidence.
- Every commit reference came from evidence.
- Every test result came from evidence.
- Every CI result came from evidence.
- Every coverage value came from evidence.
- Every artifact reference came from evidence.
- Missing evidence is explicitly identified.
- Unretrievable evidence is explicitly identified.
- No claim of successful verification is made without supporting execution evidence.

Additionally confirm:

- No file path, function name, or line reference is cited that you did not read.
- No date, person, approval, or signature appears without an evidence source.
- Nothing labelled `Evidence does not exist` was actually a retrieval failure.
- The target project's source, tests, requirements and configuration were **not modified**
  — only files under `<target-project>/output/` were written.

If any check fails, correct the document before returning it.

## Never fabricate

Never fabricate any of the following:

requirements · implementation · source files · tests · issue numbers · pull requests ·
commits · CI runs · CI results · coverage · test results · artifacts · approvals ·
configuration information · dates · personnel · signatures

If information cannot be established from evidence, mark it as missing, unavailable, or
ambiguous.

## Source references

Where practical, every important claim in a generated document should identify its
evidence source. Use concrete, checkable references:

```
Source:        docs/requirements.md
Implementation: src/hello.py
Test:           tests/test_hello.py
Issue:          GitHub Issue #3
Verification:   GitHub check run for commit <SHA>
```

Prefer a reference precise enough for an auditor to reopen it independently — a path plus
section or line range, an issue or PR number, a full commit SHA, a run or check
identifier.

**Do not invent references.** A claim you cannot source is a claim to be relabelled, not
decorated with a plausible path.

## Reporting back

When the analysis is complete, report:

1. The paths of the documents written.
2. The evidence inventory summary, including anything that could not be retrieved.
3. The gaps found, stated as findings rather than defects.
4. Any limitation that constrained the analysis.

State limitations plainly and up front. A DTE record's value comes from being trustworthy
about what it does not know.

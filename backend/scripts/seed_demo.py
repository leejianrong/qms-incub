"""Seed a demo compliance dataset through the real HTTP API, so the console
looks like ui-reference/QMS Console.dc.html instead of an empty database.

Creates one QMS standard with clauses/requirements spanning the six fixed
process steps (V10), five projects modeled on the reference mock (one left
unclassified to show that pre-wizard state), self-attests a realistic slice
of each classified project's todos so the dashboard shows a spread of
compliance percentages, and publishes a handful of blog posts + FAQ entries
adapted from the same mock.

Idempotent: re-running matches existing standards/projects/content by name
and skips creating duplicates, so this is safe to run repeatedly against a
DB that already has this demo data (or partial runs from a failed attempt).
It does NOT touch the document/RAG corpus (ADR-0012) — that's `make seed` /
the synthetic-corpus walkthrough's job, not this script's.

Usage (needs `make up` running, or invoked via `make seed-demo`, which
passes the right --api-base for you):
    cd backend && uv run python scripts/seed_demo.py --api-base http://localhost:5173/api
    # --api-base default below only reachable via `make backend-dev` (ADR-0017):
    cd backend && uv run python scripts/seed_demo.py
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

import httpx

STANDARD_NAME = "Software QMS Standard (Rev. 4.2)"
STANDARD_DESCRIPTION = (
    "In-house QMS controls a project works through from initiation to "
    "closure, tailored by risk tier at classification time."
)

# One clause per fixed process step (Q41), same six steps GET /process-steps
# serves. Ordering matches that step's position.
CLAUSES: list[tuple[str, int, str]] = [
    (
        "initiation",
        0,
        "Initiation — establish the need, secure approval to build in-house, "
        "and open the project record.",
    ),
    (
        "design",
        1,
        "Design — prepare and endorse the Authorization of Requirement (AOR) "
        "and the risk management plan.",
    ),
    (
        "build",
        2,
        "Build — baseline the requirements, apply coding standards, and gate the pipeline.",
    ),
    (
        "test",
        3,
        "Test — verify against the baselined requirements and complete acceptance testing.",
    ),
    (
        "deploy",
        4,
        "Deploy — obtain release authorisation and complete any required accreditation.",
    ),
    (
        "closure",
        5,
        "Closure — complete the post-implementation review against baselined OKRs.",
    ),
]

# Cumulative by design: every "low" requirement also applies at medium/high,
# every "medium" one also applies at high — mirrors a real QMS adding
# controls as risk goes up rather than swapping them out.
REQUIREMENTS: list[tuple[str, str, list[str]]] = [
    # step_id, description, risk_tiers
    (
        "initiation",
        "Establish the need and document why buying off-the-shelf was ruled out",
        ["low", "medium", "high"],
    ),
    (
        "initiation",
        "Open the project record and assign a project code",
        ["low", "medium", "high"],
    ),
    (
        "initiation",
        "Write the mission statement and baseline the project OKRs",
        ["low", "medium", "high"],
    ),
    (
        "initiation",
        "Secure in-house development approval from the Delivery Board",
        ["medium", "high"],
    ),
    ("design", "Prepare the Authorization of Requirement (AOR) pack", ["medium", "high"]),
    (
        "design",
        "Route the AOR for endorsement by the System Owner and QA Office",
        ["medium", "high"],
    ),
    ("design", "Draft the risk management plan", ["medium", "high"]),
    ("design", "Complete security categorisation and threat assessment", ["high"]),
    (
        "design",
        "Complete a privacy impact assessment for personal data processing",
        ["high"],
    ),
    (
        "build",
        "Baseline the requirements before build starts",
        ["low", "medium", "high"],
    ),
    (
        "build",
        "Apply coding standards and mandatory peer review",
        ["low", "medium", "high"],
    ),
    ("build", "Configure automated quality gates in the CI pipeline", ["medium", "high"]),
    (
        "test",
        "Produce a test plan traced to requirement IDs",
        ["low", "medium", "high"],
    ),
    (
        "test",
        "Complete user acceptance testing and sign the acceptance record",
        ["medium", "high"],
    ),
    (
        "deploy",
        "Obtain release authorisation from the System Owner",
        ["low", "medium", "high"],
    ),
    ("deploy", "Complete accreditation review for internet-facing systems", ["high"]),
    (
        "closure",
        "Complete the post-implementation review against baselined OKRs",
        ["low", "medium", "high"],
    ),
]


@dataclass
class DemoProject:
    name: str
    blurb: str
    # None leaves the project unclassified (pre-wizard state, like the
    # mock's Sentinel Ops Portal). Otherwise: (data_sensitivity_high,
    # customer_facing, regulatory_exposure).
    wizard_answers: tuple[bool, bool, bool] | None
    # Fraction of the generated todos (earliest process steps first) to
    # self-attest, so the dashboard shows projects at different stages.
    attest_fraction: float = 0.0


PROJECTS: list[DemoProject] = [
    DemoProject(
        name="Sentinel Ops Portal",
        blurb=(
            "Replacement operations console for the duty watch floor. "
            "Internal only, first release targeted November."
        ),
        wizard_answers=None,
    ),
    DemoProject(
        name="Atlas Claims Engine",
        blurb=(
            "Decisioning service behind claims intake. Partner-facing "
            "through the gateway, processes claimant data."
        ),
        wizard_answers=(True, True, True),  # -> high
        attest_fraction=0.55,
    ),
    DemoProject(
        name="Harbour Rostering",
        blurb=(
            "Shift and leave rostering for port operations. Internal only, "
            "subject to award/labour compliance."
        ),
        wizard_answers=(False, False, True),  # -> medium
        attest_fraction=0.35,
    ),
    DemoProject(
        name="Beacon Field App",
        blurb=(
            "Offline-first inspection app for field crews. Internet-facing, "
            "captures photographic evidence of crew members."
        ),
        wizard_answers=(True, True, False),  # -> medium
        attest_fraction=0.7,
    ),
    DemoProject(
        name="Ledger Reconciliation Tool",
        blurb=(
            "Nightly reconciliation between the finance ledger and three "
            "source systems. Internal, single release."
        ),
        wizard_answers=(True, False, True),  # -> medium
        attest_fraction=1.0,
    ),
]

# Adapted from ui-reference/QMS Console.dc.html's POSTS fixture — fictional
# demo content, not real QMS guidance.
BLOG_POSTS: list[tuple[str, str]] = [
    (
        "Rev. 4.2 cuts eleven artifacts from the initiation phase",
        "Forty post-implementation reviews said the same thing in different words: initiation "
        "asked for paperwork that restated the AOR. Teams wrote it, owners skimmed it, auditors "
        "ignored it. Rev. 4.2 removes eleven such artifacts.\n\n"
        "What replaces them is a single tailored control set, generated from the AOR pack and "
        "three clarification questions, then endorsed with the AOR. The tailoring decision — "
        "including anything argued out of scope — is now the auditable record for the phase.\n\n"
        "The trade is deliberate. Fewer documents means the ones that remain get read properly, "
        "and it means a weak AOR blocks more than it used to. Expect initiation to feel "
        "front-loaded and the middle of the process to feel considerably lighter.",
    ),
    (
        "Why in-house approvals get returned",
        "The Delivery Board is not sceptical of in-house development. It is sceptical of "
        "five-year sustainment costs that appear as a single line reading “internal effort”.\n\n"
        "Of fourteen submissions returned since March, nine were returned for the same reason: "
        "the options analysis compared licence cost against build cost, with no accounting for "
        "maintenance, on-call, or the eventual migration when the original team disperses.\n\n"
        "The workbook in step 1 exists to make that comparison mechanical. Fill it honestly, and "
        "a genuinely justified in-house build survives its first reading.",
    ),
    (
        "Secrets in pipelines are still our biggest finding",
        "Of the findings we raised at release gates last year, 38% were credentials committed to "
        "a repository or exposed in a build log. Not novel attacks — configuration mistakes made "
        "under deadline pressure.\n\n"
        "The mitigation is dull and it works: secret scanning as a blocking pre-commit hook and a "
        "blocking CI stage, short-lived workload identities instead of static keys, and build "
        "logs redacted by default. All three are in the gated release pipeline template.\n\n"
        "If you take one thing from this: treat the pipeline as a production system with "
        "production-grade access control. It has more privilege than your application does.",
    ),
    (
        "Two teams, same standard, very different experiences",
        "We followed two projects of comparable size through Rev. 4. One treated QMS steps as "
        "gates to clear before each milestone; the other treated them as documentation to "
        "assemble afterwards.\n\n"
        "The second team's cost was not in the writing. It was in rework: an endorsement refused "
        "because the risk register was empty, a UAT round rerun because acceptance criteria were "
        "never baselined, and an accreditation pack assembled from memory.\n\n"
        "There is no clever version of this finding. Engage a step while you are doing the work "
        "it describes and the artifact is a five-minute export. Engage it afterwards and you are "
        "reconstructing evidence.",
    ),
]

# Adapted from the same mock's FAQS fixture.
FAQ_ENTRIES: list[tuple[str, str]] = [
    (
        "What is the difference between in-house development approval and AOR approval?",
        "The first permits you to build rather than buy; the second fixes what you are building "
        "and which controls apply. They are separate gates with different authorities, and the "
        "second is usually returned when the first was argued loosely — the AOR inherits the "
        "scope you claimed in the options analysis.",
    ),
    (
        "How long do approvals actually take?",
        "Each approval step shows its authority and target turnaround: 10 working days for the "
        "Delivery Board and the risk plan, 8 for AOR endorsement, 5 for release authorisation. "
        "The dashboard shows anything sitting longer than its target.",
    ),
    (
        "What counts as evidence for a step?",
        "The artifact the work actually produced: a pipeline run, a signed approval, a test "
        "result export, a completed form. Summaries written after the fact do not count, and "
        "neither do screenshots of tooling. Anything uploaded is version-stamped and visible to "
        "the audit trail.",
    ),
    (
        "How do I reach the owner of a step?",
        "Comment on the todo. Every todo is visible to the QA Office, so you do not re-explain "
        "the project, and the next reviewer can read the history.",
    ),
]


def _get(client: httpx.Client, path: str) -> Any:
    response = client.get(path)
    response.raise_for_status()
    return response.json()


def _post(
    client: httpx.Client,
    path: str,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
) -> Any:
    response = client.post(path, json=json, files=files)
    if not response.is_success:
        raise RuntimeError(f"POST {path} -> {response.status_code}: {response.text}")
    return response.json()


def seed_standard(client: httpx.Client) -> dict[str, str]:
    """Returns {process_step_id: clause_id}."""
    standards = _get(client, "/standards")
    existing = next((s for s in standards if s["name"] == STANDARD_NAME), None)
    if existing is None:
        existing = _post(
            client, "/standards", {"name": STANDARD_NAME, "description": STANDARD_DESCRIPTION}
        )
        print(f"  created standard {existing['id']}")
    else:
        print(f"  standard already exists ({existing['id']})")
    standard_id = existing["id"]

    clauses = _get(client, f"/standards/{standard_id}/clauses")
    step_to_clause: dict[str, str] = {}
    for step_id, ordering, text in CLAUSES:
        existing_clause = next((c for c in clauses if c["ordering"] == ordering), None)
        if existing_clause is None:
            existing_clause = _post(
                client, f"/standards/{standard_id}/clauses", {"ordering": ordering, "text": text}
            )
            print(f"    created clause for {step_id}")
        step_to_clause[step_id] = existing_clause["id"]

    for step_id, description, risk_tiers in REQUIREMENTS:
        clause_id = step_to_clause[step_id]
        existing_reqs = _get(client, f"/clauses/{clause_id}/requirements")
        if any(r["description"] == description for r in existing_reqs):
            continue
        _post(
            client,
            f"/clauses/{clause_id}/requirements",
            {"description": description, "risk_tiers": risk_tiers, "process_step_id": step_id},
        )
    print(f"  {len(REQUIREMENTS)} requirements ensured across {len(CLAUSES)} clauses")
    return step_to_clause


def seed_projects(client: httpx.Client, process_steps: list[dict[str, Any]]) -> None:
    step_ordering = {s["id"]: s["ordering"] for s in process_steps}
    projects = _get(client, "/projects")

    for demo in PROJECTS:
        existing = next((p for p in projects if p["name"] == demo.name), None)
        if existing is None:
            existing = _post(client, "/projects", {"name": demo.name})
            print(f"  created project {demo.name!r} ({existing['id']})")
        else:
            print(f"  project {demo.name!r} already exists ({existing['id']})")

        if demo.wizard_answers is None:
            continue

        detail = _get(client, f"/projects/{existing['id']}")
        project, todos = detail["project"], detail["todos"]

        if project["risk_tier"] is None:
            data_sensitivity_high, customer_facing, regulatory_exposure = demo.wizard_answers
            detail = _post(
                client,
                f"/projects/{existing['id']}/classify",
                {
                    "answers": {
                        "data_sensitivity_high": data_sensitivity_high,
                        "customer_facing": customer_facing,
                        "regulatory_exposure": regulatory_exposure,
                    }
                },
            )
            project, todos = detail["project"], detail["todos"]
            print(f"    classified as {project['risk_tier']} -> {len(todos)} todos")
        else:
            print(f"    already classified as {project['risk_tier']} ({len(todos)} todos)")

        pending = [t for t in todos if t["status"] != "complied"]
        pending.sort(key=lambda t: step_ordering.get(t["process_step_id"], 99))
        target_attested = round(len(todos) * demo.attest_fraction)
        already_attested = len(todos) - len(pending)
        to_attest = max(0, target_attested - already_attested)
        for todo in pending[:to_attest]:
            evidence = b"Self-attested evidence for demo seeding.\n"
            client.post(
                f"/todos/{todo['id']}/artifacts",
                files={"file": ("evidence.txt", evidence, "text/plain")},
            ).raise_for_status()
        if to_attest:
            print(f"    self-attested {to_attest} todo(s)")


def seed_content(client: httpx.Client) -> None:
    posts = _get(client, "/blog-posts")
    for title, body in BLOG_POSTS:
        existing = next((p for p in posts if p["title"] == title), None)
        if existing is None:
            existing = _post(client, "/blog-posts", {"title": title, "body": body})
            print(f"  created blog post {title!r}")
        if existing.get("published_at") is None:
            _post(client, f"/blog-posts/{existing['id']}/publish")
            print(f"    published {title!r}")

    faqs = _get(client, "/faq-entries")
    for question, answer in FAQ_ENTRIES:
        existing = next((f for f in faqs if f["question"] == question), None)
        if existing is None:
            existing = _post(client, "/faq-entries", {"question": question, "answer": answer})
            print(f"  created FAQ entry {question!r}")
        if existing.get("published_at") is None:
            _post(client, f"/faq-entries/{existing['id']}/publish")
            print(f"    published {question!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://localhost:8000")
    args = parser.parse_args()

    with httpx.Client(base_url=args.api_base, timeout=30.0) as client:
        print("Seeding compliance standard/clauses/requirements...")
        seed_standard(client)

        print("Seeding demo projects...")
        process_steps = _get(client, "/process-steps")
        seed_projects(client, process_steps)

        print("Seeding blog posts and FAQ entries...")
        seed_content(client)

    print("Done.")


if __name__ == "__main__":
    main()

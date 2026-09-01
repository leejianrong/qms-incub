# RAG Policy Compliance Q&A Test Set

Perspective: control operators and evidence owners who read the policies to determine what they must do or produce to be compliant. The questions are intentionally not written from an auditor perspective.

Total pairs: 110 (100 policy-grounded compliance questions + 10 guardrail questions where the requested detail is not specified).


## POL-001 — Software Change Management Policy

### QA-001 — §4.1
**Persona:** Requester  
**Question:** I am preparing a production change request. What do I need to include before it can be queued for CAB review?  
**Expected answer:** Include, at minimum, a description of the change, the systems and customer segments affected, testing already performed, the planned deployment window, and an explicit rollback plan. The request also needs the business justification. Any bundled code must already have passed the POL-003 review gates; otherwise the request is returned without risk classification.  
**Policy artifacts/records:** Change request; linked reviewed code/PR evidence  
**Difficulty:** direct  
**Tags:** change-request, CAB, required-fields

### QA-002 — §2; §4.4
**Persona:** Requester / Implementer  
**Question:** We made an emergency production change during an active incident without the normal CAB approval sequence. What do we need to record afterward?  
**Expected answer:** Log the emergency change retroactively within one business day and have it reviewed by the CAB at its next scheduled session. Because it used the emergency bypass, it also requires a post-implementation review within five business days confirming the intended outcome and that the rollback plan would have worked as written.  
**Policy artifacts/records:** Emergency change record; CAB review record; post-implementation review  
**Difficulty:** multi-hop  
**Tags:** emergency-change, retroactive-record, PIR

### QA-003 — §2
**Persona:** Requester  
**Question:** We deployed code behind a feature flag that defaulted to off. Do we need a change record when we later enable the flag for production traffic?  
**Expected answer:** Yes. The policy applies when the feature flag is turned on for any production traffic. Enabling dormant code without a change record is treated as an unapproved change, even if the code itself was deployed earlier.  
**Policy artifacts/records:** Change record for feature-flag enablement  
**Difficulty:** edge-case  
**Tags:** feature-flag, production-change

### QA-004 — §4.2
**Persona:** Requester / CAB liaison  
**Question:** Our change is high risk. What approval evidence and pre-approval work must exist?  
**Expected answer:** A high-risk change requires CAB quorum approval and a rollback rehearsal in a staging environment before approval. The request must retain the CAB decision and the rollback rehearsal evidence.  
**Policy artifacts/records:** CAB approval record; staging rollback rehearsal evidence  
**Difficulty:** direct  
**Tags:** high-risk, approval, rollback

### QA-005 — §4.2; POL-006 §4.2
**Persona:** Requester  
**Question:** My production change provisions or modifies production credentials. What extra approval do I need before CAB approval?  
**Expected answer:** In addition to the normal change approval path, the change requires sign-off from a Security Engineer under POL-006 before the CAB may approve it.  
**Policy artifacts/records:** Security Engineer sign-off; change record  
**Difficulty:** multi-hop  
**Tags:** credentials, security-signoff, cross-policy

### QA-006 — §3
**Persona:** Requester / CAB approver  
**Question:** Can the same person submit a low-risk change and approve it for the CAB?  
**Expected answer:** No. One person may hold multiple roles on a low-risk change, but the Requester and the CAB approver must always be different people. The decision record must identify the approver and timestamp.  
**Policy artifacts/records:** Change decision record with requester and approver identities  
**Difficulty:** edge-case  
**Tags:** separation-of-duties, approval

### QA-007 — §4.6
**Persona:** Requester  
**Question:** I perform the same low-risk certificate rotation regularly. What evidence do I need if it has been designated a Standard Change?  
**Expected answer:** Log each occurrence against the CAB-approved Standard Change template and proceed to scheduling without a fresh risk classification. The Standard Change designation itself is reviewed annually, and immediately after any incident traced to that change type. 

**Policy artifacts/records:** Standard Change template/record; change calendar entry; annual designation review  
**Difficulty:** direct  
**Tags:** standard-change, pre-approved

### QA-008 — §4.5
**Persona:** Requester  
**Question:** We need to deploy during a published blackout period. What can proceed and what must be documented if we need an exception?  
**Expected answer:** Only low-risk changes or changes required to remediate an active incident may proceed by default; medium- and high-risk changes are deferred. A discretionary exception requires CAB chair approval, and the exception must be logged with the specific business justification weighed against the cost of deferral.  
**Policy artifacts/records:** Change calendar; blackout exception decision and justification  
**Difficulty:** edge-case  
**Tags:** blackout, exception

### QA-009 — §4.7; §4.14
**Persona:** Lead Requester  
**Question:** Our change spans several services owned by different teams. How should I package the request and determine the risk level?  
**Expected answer:** Submit one change request with a lead Requester and each affected team’s Implementer listed separately. Obtain sign-off from every listed Implementer before CAB review. The CAB classifies the request using the highest-risk system touched; ambiguous classifications are resolved at the higher plausible level.  
**Policy artifacts/records:** Single cross-team change request; implementer sign-offs  
**Difficulty:** multi-hop  
**Tags:** cross-team, risk-classification

### QA-010 — §3; §4.8; §4.11; §5
**Persona:** Change process owner  
**Question:** What records need to exist so our production changes are traceable and how long are they retained?  
**Expected answer:** Requests and decisions must be tracked in the change management system, with approval, rejection, or emergency-bypass decisions recording the decision-maker and timestamp. Closed records should reflect what was actually deployed, including systems, approver, and verification evidence. Change records, CAB decisions, and post-implementation review findings are retained for at least three years.  
**Policy artifacts/records:** Change management system records; CAB decisions; verification evidence; PIR findings  
**Difficulty:** multi-hop  
**Tags:** audit-trail, retention, evidence


## POL-002 — Secure Software Development Lifecycle Policy

### QA-011 — §4.1
**Persona:** Software Engineer / Engineering Manager  
**Question:** Before we start building an in-scope service, what security design artifacts do we need?  
**Expected answer:** Document the system’s trust boundaries, data flows, and the classification of the data it will handle. Use that material in a Security Engineer-facilitated threat-modeling session, then attach a written record of identified threats and the mitigation for each to the project design documentation.  
**Policy artifacts/records:** Design documentation; threat-model record with threats and mitigations  
**Difficulty:** direct  
**Tags:** threat-model, design, data-classification

### QA-012 — §4.1
**Persona:** Software Engineer  
**Question:** Our threat model found an unmitigated high-severity threat. Can we start implementation while the mitigation is figured out?  
**Expected answer:** No. A design with an unmitigated high-severity threat may not proceed to Build until the mitigation is designed, even if that requires revisiting the design.  
**Policy artifacts/records:** Threat-model finding and mitigation design  
**Difficulty:** edge-case  
**Tags:** high-severity, build-gate

### QA-013 — §4.2; POL-006 §4.1
**Persona:** Software Engineer / CI owner  
**Question:** How should we provide credentials used by the build pipeline?  
**Expected answer:** Provision build-pipeline credentials under the access-control process in POL-006 rather than embedding them directly in build scripts. The resulting access request/provisioning record should show the approved credential access.  
**Policy artifacts/records:** IAM access/provisioning record; build configuration without embedded credentials  
**Difficulty:** multi-hop  
**Tags:** build-credentials, least-privilege, cross-policy

### QA-014 — §4.2
**Persona:** Software Engineer  
**Question:** Can our production build pull a dependency directly from a public package registry?  
**Expected answer:** No. Dependencies used in the build must come through an approved internal package mirror so they pass the mirror’s vetting step before reaching a production build.  
**Policy artifacts/records:** Build/dependency configuration showing approved internal mirror  
**Difficulty:** direct  
**Tags:** supply-chain, package-mirror

### QA-015 — §4.3
**Persona:** QA Engineer  
**Question:** What security testing evidence is required for each release candidate?  
**Expected answer:** Run the automated security regression suite against every release candidate, covering at least the OWASP Top 10 risk categories. Retain the security test results. If production-derived test data is used, it must first be classified and handled under POL-007.  
**Policy artifacts/records:** Security regression test results; test-data classification/handling record if applicable  
**Difficulty:** multi-hop  
**Tags:** security-testing, release-candidate, OWASP

### QA-016 — §4.3
**Persona:** QA Engineer / Product Manager  
**Question:** A security test finds a high-severity issue in the release candidate. Can the Product Manager accept it with a future deadline?  
**Expected answer:** No. Critical or high-severity findings block the release candidate outright. Only lower-severity findings may be accepted with a documented remediation deadline at the Product Manager’s discretion.  
**Policy artifacts/records:** Security finding; release-block status; remediation deadline for lower severity only  
**Difficulty:** edge-case  
**Tags:** finding-severity, release-gate

### QA-017 — §4.4
**Persona:** Software Engineer / SRE  
**Question:** We changed authentication or authorization code. What post-deployment evidence do we need?  
**Expected answer:** Monitor anomalous authentication patterns and error-rate spikes for at least 72 hours after the change. The monitoring evidence should cover that full window.  
**Policy artifacts/records:** 72-hour post-deployment monitoring evidence  
**Difficulty:** direct  
**Tags:** authentication, monitoring, 72-hours

### QA-018 — §4.5
**Persona:** Software Engineer  
**Question:** What do I need to record when introducing a third-party or open-source component?  
**Expected answer:** Add every introduced component to the project SBOM, including its version and license. If it has had no maintained upstream release in the past two years, obtain explicit Security Engineer sign-off before introducing it.  
**Policy artifacts/records:** SBOM entry with version/license; Security Engineer sign-off if stale upstream  
**Difficulty:** direct  
**Tags:** SBOM, open-source, dependency

### QA-019 — §4.5
**Persona:** Service owner  
**Question:** A dependency already in our SBOM is later found to have a newly disclosed critical vulnerability. Can remediation wait for our normal release schedule?  
**Expected answer:** No. A newly disclosed critical vulnerability in an SBOM component triggers out-of-cycle remediation regardless of the project’s current release schedule.  
**Policy artifacts/records:** Vulnerability-feed finding; out-of-cycle remediation record  
**Difficulty:** edge-case  
**Tags:** vulnerability, SBOM, remediation

### QA-020 — §2; §5
**Persona:** Service owner  
**Question:** How long do we need to retain threat-model and security-test evidence, and does an internal tool get a full exemption?  
**Expected answer:** Threat-modeling records and security test results are retained for the lifetime of the service plus one year. Internal tooling with no external exposure and no customer-data access is exempt only from the threat-modeling requirement; it still must meet the secure-build and security-testing requirements.  
**Policy artifacts/records:** Threat-model records; security test results  
**Difficulty:** multi-hop  
**Tags:** retention, internal-tool, scope


## POL-003 — Code Review and Quality Gate Policy

### QA-021 — §2; §3
**Persona:** Software Engineer / PR Author  
**Question:** Does every code change to a production repository need a reviewer, even if I am very senior or the change is tiny?  
**Expected answer:** Yes. Every in-scope code change requires at least one approval from someone other than the author, regardless of size or author seniority.  
**Policy artifacts/records:** Pull request approval record  
**Difficulty:** direct  
**Tags:** code-review, separation-of-duties

### QA-022 — §2
**Persona:** Software Engineer / PR Author  
**Question:** My pull request only changes documentation or test fixtures. What gates still apply?  
**Expected answer:** It still requires at least one reviewer approval, but documentation-only changes and test-fixture-only changes are exempt from the static-analysis and coverage thresholds that apply to production code paths.  
**Policy artifacts/records:** PR approval record; CI evidence as applicable  
**Difficulty:** edge-case  
**Tags:** documentation, test-fixtures, quality-gates

### QA-023 — §2
**Persona:** Software Engineer  
**Question:** Do generated source files need manual review?  
**Expected answer:** Generated code is exempt from manual review if the generator itself is a reviewed, version-pinned dependency. In that case, the review burden falls on whoever last changed the generator configuration.  
**Policy artifacts/records:** Generator dependency/version evidence; reviewed generator-configuration change  
**Difficulty:** edge-case  
**Tags:** generated-code, review-exception

### QA-024 — §4.1
**Persona:** PR Author  
**Question:** What information should I put in the pull request description?  
**Expected answer:** Describe the change, state how it was tested, and, where the change is part of a larger initiative, link the associated change request under POL-001.  
**Policy artifacts/records:** Pull request description; linked change request when applicable  
**Difficulty:** direct  
**Tags:** PR-description, testing, traceability

### QA-025 — §4.1
**Persona:** PR Author  
**Question:** My pull request touches about 600 lines of production code. Is there a policy expectation about how I structure it?  
**Expected answer:** A pull request touching more than roughly 400 lines of production code should be split into smaller independently reviewable pull requests wherever the change allows it.  
**Policy artifacts/records:** Pull request(s) structured for review  
**Difficulty:** edge-case  
**Tags:** large-PR, reviewability

### QA-026 — §3; §4.2
**Persona:** PR Author / CI owner  
**Question:** What quality gates must pass before a production-code pull request is eligible to merge?  
**Expected answer:** At least one non-author reviewer approval is required; automated test coverage must not decrease versus the target branch; static analysis must have zero unresolved critical or high-severity findings; and all required CI checks must pass. Failed required CI checks make the PR ineligible for human review until they pass.  
**Policy artifacts/records:** CI checks; coverage result; static-analysis result; reviewer approval  
**Difficulty:** multi-hop  
**Tags:** CI, coverage, static-analysis, merge-gate

### QA-027 — §4.2
**Persona:** Reviewer  
**Question:** I do not understand an unfamiliar subsystem touched by a pull request. What should I record or do instead of approving it?  
**Expected answer:** State that you lack sufficient context and request a second reviewer with the relevant background rather than approving out of deference to the author.  
**Policy artifacts/records:** PR review comment; additional reviewer request/approval  
**Difficulty:** direct  
**Tags:** reviewer-context, second-reviewer

### QA-028 — §4.3
**Persona:** PR Author  
**Question:** We need to revert a merged change. Can we direct-push the revert to main?  
**Expected answer:** No. The revert must go through a new pull request following the same review cycle and quality gates as any other change.  
**Policy artifacts/records:** Revert pull request; review and CI records  
**Difficulty:** edge-case  
**Tags:** revert, direct-push

### QA-029 — §4.4
**Persona:** On-call engineer / Engineering Manager  
**Question:** During an active incident, what can we bypass in code review and what evidence still has to exist?  
**Expected answer:** The manual review requirement may be bypassed with explicit sign-off from the on-call Engineering Manager recorded on the pull request. The change still passes through CI, and any skipped check must be explicitly named in the PR description rather than skipped silently.  
**Policy artifacts/records:** Emergency PR; Engineering Manager sign-off; CI results; named skipped checks  
**Difficulty:** multi-hop  
**Tags:** emergency, review-bypass, CI

### QA-030 — §3; §4.5; §5
**Persona:** Engineering Manager  
**Question:** What review-process records should we retain and monitor over time?  
**Expected answer:** Pull request history, including review comments and approval records, is retained indefinitely in source control. Reviewers are expected to respond within one business day; Engineering Managers track median time to first review and median time to merge, and quarterly sample merged PRs for substantive review quality.  
**Policy artifacts/records:** PR history; review comments/approvals; team review metrics; quarterly review sample  
**Difficulty:** multi-hop  
**Tags:** retention, review-metrics, quality-review


## POL-004 — Release and Deployment Management Policy

### QA-031 — §4.1
**Persona:** Release Manager  
**Question:** What traceability evidence must exist before a release candidate can proceed past branch freeze?  
**Expected answer:** Every production deployment must trace back to an approved change record under POL-001. A release candidate with no linked approved change record cannot proceed past branch freeze.  
**Policy artifacts/records:** Release record linked to approved change record  
**Difficulty:** direct  
**Tags:** release, change-record, traceability

### QA-032 — §4.1
**Persona:** Release Manager / QA Engineer  
**Question:** What evidence is required around branch freeze and regression testing?  
**Expected answer:** The Release Manager freezes the release branch and notifies dependent teams. QA runs the full regression suite against the frozen branch. A failing test returns the branch to the owning team and extends the freeze so unrelated changes cannot enter the release.  
**Policy artifacts/records:** Branch-freeze record/notification; full regression results  
**Difficulty:** direct  
**Tags:** branch-freeze, regression

### QA-033 — §2; §4.1
**Persona:** Release Manager / Database owner  
**Question:** Our release includes a database schema migration. What additional pre-rollout evidence do we need?  
**Expected answer:** The migration must be reviewed for backward compatibility with the currently running application version so both old and new versions can operate correctly during staged rollout.  
**Policy artifacts/records:** Schema-migration backward-compatibility review  
**Difficulty:** direct  
**Tags:** database, migration, backward-compatibility

### QA-034 — §4.2
**Persona:** SRE  
**Question:** What should we capture during the staged production rollout?  
**Expected answer:** After QA sign-off, deploy to a small slice of production traffic and monitor error rate and latency for the duration of the staged window. The initial traffic share should reflect the risk classification carried over from the change record.  
**Policy artifacts/records:** QA sign-off; staged rollout record; error/latency monitoring evidence  
**Difficulty:** multi-hop  
**Tags:** staged-rollout, monitoring, risk

### QA-035 — §3
**Persona:** Release Manager / SRE  
**Question:** What approvals are needed for staged production versus full production rollout?  
**Expected answer:** A staged production rollout requires QA sign-off. A full production rollout requires QA sign-off plus the SRE go/no-go decision.  
**Policy artifacts/records:** QA sign-off; SRE go/no-go record  
**Difficulty:** direct  
**Tags:** release-approval, go-no-go

### QA-036 — §3
**Persona:** On-call SRE  
**Question:** What rollback time targets do we need to meet and how are they measured?  
**Expected answer:** For production staged rollout, the rollback SLA is 15 minutes; for full rollout, 30 minutes. The clock runs from when a regression is confirmed until the previous version is fully restored. If the SLA cannot be met, the SRE escalates immediately.  
**Policy artifacts/records:** Rollback timing record; escalation record if SLA at risk  
**Difficulty:** direct  
**Tags:** rollback, SLA

### QA-037 — §4.3
**Persona:** On-call SRE  
**Question:** Monitoring confirms a release regression. Should I attempt a forward fix inside the release window?  
**Expected answer:** No. Initiate the rollback procedure rather than attempting a forward fix under release-window pressure. Log the rollback against the same release record because the rollback is itself a deployment.  
**Policy artifacts/records:** Rollback record linked to release; incident/rollback procedure record  
**Difficulty:** edge-case  
**Tags:** regression, rollback, release-record

### QA-038 — §4.4
**Persona:** Release Manager / Product Manager  
**Question:** What communications do we need to retain around a scheduled release?  
**Expected answer:** Notify affected internal stakeholders, including customer support and dependent teams, before the scheduled release window and again when the release completes or is rolled back. For customer-visible behavior changes, the Product Manager decides whether external release notes are needed.  
**Policy artifacts/records:** Internal release notifications; completion/rollback notification; release-note decision if applicable  
**Difficulty:** direct  
**Tags:** stakeholder-communication, release-notes

### QA-039 — §4.5
**Persona:** SRE  
**Question:** Do we have to use automated canary analysis for every service?  
**Expected answer:** No. Canary analysis is strongly recommended where supported, but not mandatory. A service without it must use the manual dashboard-watching staged-rollout procedure. If automated analysis crosses a threshold, the platform halts rollout and pages the on-call SRE.  
**Policy artifacts/records:** Canary-analysis output or manual monitoring evidence  
**Difficulty:** edge-case  
**Tags:** canary, monitoring

### QA-040 — §5
**Persona:** Release Manager  
**Question:** How long should release, rollback, and stakeholder-notification records be retained?  
**Expected answer:** Deployment and rollback records are retained for three years, matching the change-record retention period. Stakeholder notification records are retained for one year.  
**Policy artifacts/records:** Deployment records; rollback records; stakeholder notifications  
**Difficulty:** direct  
**Tags:** retention, release-evidence


## POL-005 — Incident Management and Response Policy

### QA-041 — §4.1
**Persona:** First responder  
**Question:** I think I found a production incident. What records/actions should I create immediately?  
**Expected answer:** Open an incident channel, page the on-call Site Reliability Engineer if not already paged, and post a first best-effort description of the impact. These create the initial incident record and response timeline.  
**Policy artifacts/records:** Incident channel; initial impact description; paging record  
**Difficulty:** direct  
**Tags:** incident-detection, triage

### QA-042 — §4.1
**Persona:** Incident Commander  
**Question:** How quickly do I need to make the initial severity call after being paged?  
**Expected answer:** The on-call SRE acting as Incident Commander has 15 minutes from being paged to make the initial severity call. It is acceptable to classify conservatively and downgrade later.  
**Policy artifacts/records:** Incident timeline; initial severity decision  
**Difficulty:** direct  
**Tags:** severity, 15-minutes

### QA-043 — §4.2
**Persona:** Incident Commander  
**Question:** We have a confirmed customer-data exposure. What severity and response targets apply?  
**Expected answer:** Confirmed data exposure meets the Sev1 — Critical definition. The target response is 15 minutes and the target resolution is 4 hours.  
**Policy artifacts/records:** Severity classification; incident timeline  
**Difficulty:** direct  
**Tags:** Sev1, data-exposure, targets

### QA-044 — §3
**Persona:** Incident Commander / responder  
**Question:** Can two people act as Incident Commander during the same active incident?  
**Expected answer:** No. Exactly one person holds the Incident Commander role at any given time. A handoff is allowed only if it is explicit and announced in the incident channel.  
**Policy artifacts/records:** Incident-channel handoff announcement  
**Difficulty:** edge-case  
**Tags:** incident-command, handoff

### QA-045 — §2; §3
**Persona:** Incident Commander / Security Engineer  
**Question:** The incident may involve unauthorized access or credential compromise. What extra escalation evidence do we need?  
**Expected answer:** Escalate immediately to the Security Engineer on call. The Security Engineer leads the security dimension and may invoke additional containment steps. The incident still follows the same incident lifecycle.  
**Policy artifacts/records:** Security escalation/page; incident record of containment decisions  
**Difficulty:** multi-hop  
**Tags:** security-incident, escalation

### QA-046 — §4.3
**Persona:** Incident Commander / Product Manager  
**Question:** What update cadence should our incident timeline and communications show?  
**Expected answer:** Sev1 incidents require status updates at least every 30 minutes; Sev2 every hour; Sev3 and Sev4 at each material status change. The Product Manager, in consultation with the Incident Commander, decides external publication.  
**Policy artifacts/records:** Incident status updates; external-communication decisions  
**Difficulty:** direct  
**Tags:** communication-cadence, status

### QA-047 — §4.3; POL-009 §4
**Persona:** Incident Commander / SRE  
**Question:** A Sev1 or Sev2 incident threatens an extended loss of a production data store or region. What additional decision should we record?  
**Expected answer:** Perform an assessment against the Business Continuity and Disaster Recovery Policy. The Incident Commander and on-call SRE jointly decide whether to invoke the DR plan or continue mitigation within the normal incident process.  
**Policy artifacts/records:** DR assessment; invoke/not-invoke decision  
**Difficulty:** multi-hop  
**Tags:** DR, Sev1, Sev2, cross-policy

### QA-048 — §4.4
**Persona:** Incident Commander  
**Question:** When can I mark an incident resolved?  
**Expected answer:** Only when the underlying impact has stopped and the affected service has returned to its normal operating state; a workaround alone is not enough. Announce resolution in the incident channel with a short summary of impact, duration, and mitigation.  
**Policy artifacts/records:** Resolution announcement with impact, duration, mitigation  
**Difficulty:** direct  
**Tags:** resolution, incident-record

### QA-049 — §4.4
**Persona:** Incident Commander / Engineering Manager  
**Question:** What artifact is required after a Sev1 or Sev2 incident?  
**Expected answer:** Within five business days, conduct a blameless post-incident review attended by every participating team. The written review must include a timeline, root cause or best available explanation, and follow-up actions with named owners and due dates. The Engineering Manager tracks those actions to completion.  
**Policy artifacts/records:** Post-incident review; action tracker with owners/due dates  
**Difficulty:** direct  
**Tags:** PIR, Sev1, Sev2, follow-up

### QA-050 — §4.4; POL-001
**Persona:** Engineering Manager  
**Question:** A post-incident action requires a production change. Can we implement it directly because it came from the PIR?  
**Expected answer:** No. Any follow-up action that constitutes a production change must go through the normal Software Change Management Policy. The PIR does not create an exemption.  
**Policy artifacts/records:** PIR action; linked approved change record  
**Difficulty:** edge-case  
**Tags:** post-incident, change-management, cross-policy


## POL-006 — Access Control and Least Privilege Policy

### QA-051 — §4.1
**Persona:** Employee / manager  
**Question:** What must an access request contain before IT can provision it?  
**Expected answer:** Submit it through the identity and access management system, naming the specific system or data store, the access profile requested, and a business justification. Standing production access must be justified by an actual job responsibility, not convenience.  
**Policy artifacts/records:** IAM access request  
**Difficulty:** direct  
**Tags:** access-request, least-privilege, required-fields

### QA-052 — §3; §4.2
**Persona:** Employee / manager  
**Question:** What approvals do I need for production write access or sensitive data access?  
**Expected answer:** Every request needs the requester’s manager approval. The policy’s Elevated profile for write access to production requires Manager + Security Engineer approval. Requests touching Confidential or Restricted data additionally require Data Protection Officer or delegate sign-off under §4.2.  
**Policy artifacts/records:** IAM approval chain  
**Difficulty:** multi-hop  
**Tags:** approval, production, sensitive-data

### QA-053 — §4.2
**Persona:** Manager / administrator  
**Question:** I have admin rights. Can I approve my own access request?  
**Expected answer:** No. Nobody may approve their own access request, even if they technically have the administrative rights to grant it.  
**Policy artifacts/records:** IAM approval record showing separate approver  
**Difficulty:** edge-case  
**Tags:** self-approval, separation-of-duties

### QA-054 — §4.1
**Persona:** On-call engineer  
**Question:** How should break-glass production access be provisioned during an incident?  
**Expected answer:** Request and grant it through the same access process, but time-box it by default so it automatically expires. It must not be converted into standing access merely because it was needed during an incident.  
**Policy artifacts/records:** Break-glass access request; expiry/time-box evidence  
**Difficulty:** direct  
**Tags:** break-glass, temporary-access

### QA-055 — §4.2
**Persona:** IT Support Analyst  
**Question:** After an access request is approved, what provisioning evidence should I leave behind?  
**Expected answer:** Grant exactly the approved access profile, no more and no less, and confirm completion to the requester and manager. Standard requests should be completed within one business day; break-glass requests within the active incident window.  
**Policy artifacts/records:** Provisioning record; completion confirmation  
**Difficulty:** direct  
**Tags:** provisioning, SLA, least-privilege

### QA-056 — §4.2
**Persona:** IT Support Analyst  
**Question:** A legacy system has no automated provisioning interface. Can I grant access manually?  
**Expected answer:** Yes, but only where the system genuinely has no programmatic provisioning interface. The manual grant must then be logged in the identity system so it appears in the periodic review.  
**Policy artifacts/records:** Manual system grant; matching IAM log entry  
**Difficulty:** edge-case  
**Tags:** manual-provisioning, legacy-system

### QA-057 — §4.3
**Persona:** Security Engineer / Engineering Manager  
**Question:** What evidence do we need for the quarterly access review?  
**Expected answer:** Review every access grant at least quarterly. Confirm ongoing need with the relevant Engineering Manager, use actual usage data where available, flag unjustified access for revocation, and record when the review relied on manager attestation because usage data was unavailable.  
**Policy artifacts/records:** Quarterly access review; usage evidence or attestation; revocation flags  
**Difficulty:** direct  
**Tags:** access-review, quarterly, usage-data

### QA-058 — §4.3
**Persona:** Service owner / Security Engineer  
**Question:** What evidence is required for service accounts with standing write access to production data?  
**Expected answer:** Review service-account credentials on the same quarterly access-review cycle and rotate credentials according to risk. A service account with standing write access to a production data store must be rotated at least every 90 days.  
**Policy artifacts/records:** Quarterly service-account review; credential-rotation record  
**Difficulty:** direct  
**Tags:** service-account, credential-rotation, 90-days

### QA-059 — §4.4
**Persona:** IT Support Analyst  
**Question:** When must access be revoked and how quickly do I need to confirm it?  
**Expected answer:** Revoke access immediately when a review finds it unjustified, when a role change makes it inappropriate, or when an engagement ends. IT Support confirms revocation complete the same business day it is triggered; for a termination, by the end of that business day.  
**Policy artifacts/records:** Revocation record and completion timestamp  
**Difficulty:** direct  
**Tags:** revocation, same-day

### QA-060 — §4.5; §4.6
**Persona:** Security Engineer  
**Question:** What audit trail and exception records do we need to maintain for access control?  
**Expected answer:** Log every request, approval, provisioning action, review outcome, and revocation with timestamp and actor identity, retaining those logs for at least three years. Any exception must be documented by Security, time-boxed, reviewed at least quarterly, and include an expected resolution date rather than becoming a permanent carve-out.  
**Policy artifacts/records:** IAM logs; quarterly access-control summary; exception record with expiry/resolution date  
**Difficulty:** multi-hop  
**Tags:** audit-log, retention, exception


## POL-007 — Data Classification and Handling Policy

### QA-061 — §4.2
**Persona:** Engineering Manager  
**Question:** We are creating a new data store. What classification evidence must exist before real data is written to it?  
**Expected answer:** Classify the data store at design time before real data is written. Record the classification in the system’s own documentation and in the company’s central data inventory.  
**Policy artifacts/records:** System documentation; central data inventory entry  
**Difficulty:** direct  
**Tags:** data-classification, new-store

### QA-062 — §4.1
**Persona:** Engineering Manager / Software Engineer  
**Question:** Our dataset contains both Internal and Restricted fields. What classification should the dataset carry?  
**Expected answer:** Classify the entire dataset at the level of its most sensitive element, so it is Restricted unless the sensitive field is separated into its own store with its own controls.  
**Policy artifacts/records:** Dataset/data-store classification record  
**Difficulty:** direct  
**Tags:** mixed-data, restricted

### QA-063 — §4.1
**Persona:** Data owner  
**Question:** How do I distinguish the four data tiers when documenting a dataset?  
**Expected answer:** Public is approved for unrestricted external release; Internal is non-sensitive but not for external release; Confidential would cause meaningful harm if disclosed; Restricted is subject to legal, regulatory, or contractual protection requiring the strictest controls.  
**Policy artifacts/records:** Classification record using one of the four tiers  
**Difficulty:** direct  
**Tags:** tiers, classification

### QA-064 — §4.2; POL-006 §4.2
**Persona:** Software Engineer / system owner  
**Question:** What controls must I show for Confidential or Restricted data?  
**Expected answer:** Show that the data is encrypted both at rest and in transit and that access follows the elevated approval chain in POL-006. These handling requirements apply wherever copies of the data exist.  
**Policy artifacts/records:** Encryption configuration/evidence; approved access records  
**Difficulty:** multi-hop  
**Tags:** encryption, confidential, restricted, cross-policy

### QA-065 — §4.2
**Persona:** Data analyst  
**Question:** I exported Confidential data from the production system into a spreadsheet for analysis. Can I treat the export as Internal because it is only temporary?  
**Expected answer:** No. The copy remains Confidential and must continue to meet the same encryption and access requirements as the source data.  
**Policy artifacts/records:** Classification/handling controls for the exported copy  
**Difficulty:** edge-case  
**Tags:** export, classification-inheritance

### QA-066 — §4.3; POL-008 §4
**Persona:** Product Manager / data owner  
**Question:** We already use a vendor for another purpose. Can I send it Confidential data for a new use without another vendor-risk step?  
**Expected answer:** No. Confidential or Restricted data may be shared with a third party only after the relationship and intended data use have been evaluated under POL-008. Existing use of the vendor for an unrelated purpose does not make the new sharing compliant.  
**Policy artifacts/records:** Vendor-risk evaluation/approval for the intended data use  
**Difficulty:** edge-case  
**Tags:** vendor-sharing, confidential, cross-policy

### QA-067 — §4.3
**Persona:** Data owner / IT  
**Question:** How should we document disposal of Confidential or Restricted data?  
**Expected answer:** Dispose of it according to the retention schedule attached to its classification using cryptographic erasure or physical destruction of the underlying media. Plain file deletion is not sufficient.  
**Policy artifacts/records:** Disposal/destruction record  
**Difficulty:** direct  
**Tags:** data-disposal, cryptographic-erasure

### QA-068 — §4.4
**Persona:** Engineering Manager / DPO  
**Question:** Our scanning tool found a likely government identifier in a system not classified Restricted. What compliant artifact should result?  
**Expected answer:** Route the finding to the Data Protection Officer for confirmation. If confirmed, either reclassify the system or remove the offending data, as agreed by the Engineering Manager and DPO, and retain the finding and resolution.  
**Policy artifacts/records:** Scanning finding; DPO confirmation; reclassification or removal record  
**Difficulty:** direct  
**Tags:** scanning, restricted-data, remediation

### QA-069 — §3
**Persona:** Engineering Manager / Security Engineer  
**Question:** Who sets and who can challenge or override a data classification?  
**Expected answer:** The Engineering Manager sets the initial classification. The Data Protection Officer can override it, and the Security Engineer is expected to flag classifications they believe are wrong, particularly for stores interacting with vendors or third parties.  
**Policy artifacts/records:** Classification decision/review record  
**Difficulty:** direct  
**Tags:** roles, classification-dispute

### QA-070 — §4.2
**Persona:** Software Engineer  
**Question:** What handling controls apply to Internal versus Public data?  
**Expected answer:** Internal data must remain behind authenticated access, though it does not have the same mandatory encryption-at-rest requirement as Confidential/Restricted data. Public data has no handling restriction beyond normal integrity controls.  
**Policy artifacts/records:** Authentication controls for Internal data; integrity controls for Public data  
**Difficulty:** direct  
**Tags:** internal, public, handling


## POL-008 — Vendor and Third-Party Risk Management Policy

### QA-071 — §2; §4.1
**Persona:** Product Manager / Procurement Sponsor  
**Question:** We want to run a free vendor proof of concept using a small anonymized sample of real data. Do I need vendor intake first?  
**Expected answer:** Yes. A trial or proof of concept is in scope from the moment any real company or customer data, even a small anonymized sample, is shared. Route it through vendor intake before sharing the data.  
**Policy artifacts/records:** Vendor intake request  
**Difficulty:** edge-case  
**Tags:** vendor-intake, POC, scope

### QA-072 — §4.1
**Persona:** Product Manager / Procurement Sponsor  
**Question:** What information should I provide in the vendor intake artifact?  
**Expected answer:** Describe the service, the data the vendor will touch, whether it connects to any production system, and the business justification/data flows. Security then tiers it using the data classification and obtains the standard security questionnaire covering encryption, access controls, incident history, and subprocessors.  
**Policy artifacts/records:** Vendor intake request; security questionnaire  
**Difficulty:** direct  
**Tags:** vendor-intake, questionnaire, data-flow

### QA-073 — §4; Table 2
**Persona:** Security Engineer / Procurement Sponsor  
**Question:** What due-diligence artifacts and reassessment cadence apply by vendor risk tier?  
**Expected answer:** Critical: SOC 2 Type II or equivalent, penetration test summary, right-to-audit clause, DPO sign-off, reassessed quarterly. High: SOC 2 Type II or equivalent, security questionnaire, DPO sign-off, reassessed semi-annually. Medium: security questionnaire and Security Engineer sign-off, reassessed annually. Low: standard procurement terms only, reassessed at contract renewal.  
**Policy artifacts/records:** Vendor due-diligence package; reassessment records  
**Difficulty:** multi-hop  
**Tags:** risk-tier, due-diligence, cadence

### QA-074 — §4.1
**Persona:** Security Engineer / DPO  
**Question:** A Critical or High vendor’s SOC 2 report has a material finding. Can onboarding continue without addressing it?  
**Expected answer:** Not unless the finding is either remediated or formally risk-accepted by the Data Protection Officer before onboarding proceeds. The risk acceptance should remain explicit and visible.  
**Policy artifacts/records:** SOC 2/equivalent report; finding review; DPO risk-acceptance record if applicable  
**Difficulty:** edge-case  
**Tags:** SOC2, material-finding, risk-acceptance

### QA-075 — §4.2
**Persona:** Vendor risk owner  
**Question:** What information must stay current in the vendor risk registry, and what happens if a vendor misses reassessments?  
**Expected answer:** Record each onboarded vendor’s tier, renewal date, and next reassessment date. If a vendor misses two consecutive reassessment windows, it is automatically flagged to the DPO, who decides whether to suspend new data flows until reassessment is complete.  
**Policy artifacts/records:** Vendor risk registry; overdue-reassessment flag/decision  
**Difficulty:** direct  
**Tags:** vendor-registry, reassessment

### QA-076 — §4.2
**Persona:** Product Manager / Security Engineer  
**Question:** A Medium vendor will now connect to a production pipeline handling Confidential data. Can we wait until the annual reassessment to change its tier?  
**Expected answer:** No. Re-tier the vendor when the expanded integration is proposed; it becomes at least High. The sponsoring Product Manager must flag the change to Security before the integration goes live.  
**Policy artifacts/records:** Updated intake/tier decision; vendor risk registry update  
**Difficulty:** edge-case  
**Tags:** re-tiering, scope-change, confidential

### QA-077 — §4.3; POL-009 §4
**Persona:** Security Engineer / vendor owner  
**Question:** What incident-notification evidence should our vendor arrangement require?  
**Expected answer:** The questionnaire and contract must require the vendor to notify the company within 24 hours of discovering any incident that may have affected company or customer data. Security triages it as an internal incident; if the vendor supports a service-critical system, also assess whether DR action is needed.  
**Policy artifacts/records:** Contract/questionnaire notification clause; vendor incident record; DR assessment if applicable  
**Difficulty:** multi-hop  
**Tags:** vendor-incident, 24-hours, DR

### QA-078 — §4.4
**Persona:** Security Engineer / Product Manager  
**Question:** A vendor engagement is ending. What offboarding evidence must we produce?  
**Expected answer:** Revoke the vendor’s system access within one business day and obtain written confirmation that company data was returned or securely destroyed according to POL-007. Mark the vendor registry entry offboarded rather than deleting it.  
**Policy artifacts/records:** Access-revocation record; written data return/destruction confirmation; offboarded registry entry  
**Difficulty:** multi-hop  
**Tags:** vendor-offboarding, data-destruction

### QA-079 — §4.5; §4.6
**Persona:** Legal / Security Engineer  
**Question:** What contractual and subprocessor artifacts are mandatory for a Critical or High vendor?  
**Expected answer:** The contract must include a right-to-audit clause and require equivalent data-handling and breach-notification obligations to flow down to subprocessors. Critical/High vendors must disclose their full subprocessor list at onboarding and notify the company at least 30 days before adding a new subprocessor that will touch company data.  
**Policy artifacts/records:** Contract with right-to-audit/flow-down clauses; subprocessor list; change notifications  
**Difficulty:** multi-hop  
**Tags:** contract, right-to-audit, subprocessor

### QA-080 — §4.7; §4.9
**Persona:** Security Engineer / SRE / Procurement Sponsor  
**Question:** How should we document a cloud infrastructure provider or a payment processor that touches raw card data?  
**Expected answer:** Cloud compute, managed database, and CDN providers that directly host/run production infrastructure are always Critical and require an SRE architecture review for undocumented single points of failure. Vendors that store/process/transmit raw cardholder data are also always Critical and must provide current PCI DSS v4.0 evidence in addition to the standard Critical-tier SOC 2 evidence.  
**Policy artifacts/records:** Critical-tier registry entry; SRE architecture review for infrastructure provider; PCI DSS evidence for card processor  
**Difficulty:** multi-hop  
**Tags:** critical-vendor, cloud, PCI


## POL-009 — Business Continuity and Disaster Recovery Policy

### QA-081 — §2; §4 Table 2
**Persona:** Engineering Manager / SRE  
**Question:** What recovery-plan and annual-test artifacts are required for Tier 1, Tier 2, and Tier 3 systems?  
**Expected answer:** Tier 1 systems require a recovery plan and a live failover exercise at least annually. Tier 2 systems require a recovery plan and at least an annual tabletop exercise; live testing is optional. Tier 3 does not require a full DR plan or mandated test, but must have a documented restore-from-backup procedure.  
**Policy artifacts/records:** Per-system recovery plan; annual test record; Tier 3 restore procedure  
**Difficulty:** direct  
**Tags:** service-tier, annual-test, DR-plan

### QA-082 — §4 Table 2
**Persona:** System owner  
**Question:** If our Tier 1 system has no approved system-specific override, what RTO and RPO should our recovery plan and test results use?  
**Expected answer:** Use the company defaults: a 4-hour RTO and a 15-minute RPO for Tier 1 systems.  
**Policy artifacts/records:** Recovery plan with RTO/RPO; test results against targets  
**Difficulty:** direct  
**Tags:** RTO, RPO, Tier1

### QA-083 — §2
**Persona:** Engineering Manager  
**Question:** How do we show that our Tier 1 recovery plan is not dependent on one person?  
**Expected answer:** Name at least two people capable of executing each critical recovery step in the plan.  
**Policy artifacts/records:** Recovery plan with backup executors/owners  
**Difficulty:** direct  
**Tags:** key-person-risk, recovery-plan

### QA-084 — §4.1; §4.2
**Persona:** Incident Commander / system owner  
**Question:** Once a DR event is declared, what should the recovery artifact show?  
**Expected answer:** The documented recovery plan should identify the failover target, traffic-redirection steps, and verification checks. The owning team executes it after the Incident Commander declares the DR event; customer-facing communications require Product Manager approval.  
**Policy artifacts/records:** DR declaration; recovery plan/runbook; failover verification; communication approval  
**Difficulty:** multi-hop  
**Tags:** DR-activation, failover, runbook

### QA-085 — §4.5
**Persona:** System owner  
**Question:** When do we need to review or update a Tier 1/Tier 2 recovery plan?  
**Expected answer:** Review it whenever the system undergoes a material architecture change and at least once per year even if no such change occurs. Log the review date alongside the annual test date.  
**Policy artifacts/records:** Recovery-plan review record/date  
**Difficulty:** direct  
**Tags:** plan-maintenance, architecture-change

### QA-086 — §4.8; POL-001
**Persona:** SRE / Engineering Manager  
**Question:** We are scheduling a live failover test. What change-control evidence is required, and what if the test is aborted?  
**Expected answer:** Schedule the live failover test with the same change-management rigor as a production change, including a defined rollback point. If the test is aborted, still log it as that year’s completed test and record the abort as a finding that must be addressed before the next attempt.  
**Policy artifacts/records:** Approved change record for test; rollback point; DR test result; abort finding if applicable  
**Difficulty:** multi-hop  
**Tags:** live-failover, change-management, test-finding

### QA-087 — §4.9
**Persona:** Tier 1 system owner  
**Question:** What backup-restore evidence must we produce outside the annual failover test?  
**Expected answer:** At least quarterly, restore from an actual backup into an isolated environment and verify data integrity. A failed exercise is treated as a Sev2-equivalent finding and is not closed until a subsequent restore-and-verify exercise for the same system succeeds.  
**Policy artifacts/records:** Quarterly restore-and-verify record; integrity checks; remediation/retest evidence  
**Difficulty:** direct  
**Tags:** backup, restore-test, quarterly

### QA-088 — §4.10
**Persona:** System owner / SRE  
**Question:** What dependency information needs to be in a Tier 1 recovery plan and annual test?  
**Expected answer:** Document each critical internal and external dependency and what happens if it is unavailable. Include the on-call team for internally owned dependencies in the annual test. For Critical-tier vendor dependencies, document the vendor’s published RTO/RPO and the company contingency if the vendor misses them.  
**Policy artifacts/records:** Recovery-plan dependency section; cross-team test participation; vendor RTO/RPO and contingency  
**Difficulty:** multi-hop  
**Tags:** dependencies, vendor, cross-team

### QA-089 — §4.7
**Persona:** Communications lead / Product Manager  
**Question:** What communication evidence should exist during an active DR event?  
**Expected answer:** The Incident Commander designates a communications lead. Public status/customer updates occur at least every 30 minutes while the DR event is active, and internal technical communications are kept on a separate channel from customer-facing updates.  
**Policy artifacts/records:** Communications-lead designation; status-page/customer updates; separate internal incident channel  
**Difficulty:** direct  
**Tags:** DR-communication, 30-minutes

### QA-090 — §4.12
**Persona:** SRE / Engineering Manager  
**Question:** What must the annual DR readiness report contain, especially for a system that missed its test?  
**Expected answer:** Cover every Tier 1 and Tier 2 system, stating whether its required test was completed, the RTO/RPO actually achieved versus target, and any open findings from real events or tests. A system that missed its test is listed as non-compliant, and its Engineering Manager presents a remediation timeline to the CAB.  
**Policy artifacts/records:** Annual DR readiness report; CAB review; remediation timeline for non-compliant systems  
**Difficulty:** direct  
**Tags:** annual-report, non-compliance, CAB


## POL-010 — IT Onboarding and Offboarding Policy

### QA-091 — §4 Table 2; §4.1
**Persona:** HR / hiring manager / IT Support  
**Question:** What onboarding artifacts and timing do we need for a normal new hire?  
**Expected answer:** HR should create the new-hire record at least five business days before the start date where possible. Baseline access—identity provider, email, chat, and device management—is provisioned from that HR record by the start date. The hiring manager submits separate role-specific access requests, which are provisioned under POL-006 and have a three-business-day SLA from approval.  
**Policy artifacts/records:** HR new-hire record; baseline provisioning record; role-specific access requests  
**Difficulty:** multi-hop  
**Tags:** onboarding, new-hire, SLA

### QA-092 — §4.9
**Persona:** HR / IT Support  
**Question:** What is different for an international new hire from an evidence/timing perspective?  
**Expected answer:** Use the same baseline and role-specific workflow, but HR is expected to create the new-hire record at least ten business days before the start date so laptop shipping and hardware-token access can begin earlier. Where local law requires a countersigned contract first, withhold production access until the Engineering Manager confirms execution.  
**Policy artifacts/records:** HR new-hire record; shipping/token record; contract-execution confirmation if applicable  
**Difficulty:** edge-case  
**Tags:** international, onboarding

### QA-093 — §4 Table 2; §4.2
**Persona:** Engineering Manager / IT Support  
**Question:** An employee changes roles internally. What should the access records show?  
**Expected answer:** Treat the move as partial offboarding plus partial onboarding. The new manager requests access for the new role, the previous manager identifies old-role access for removal, and old access is not carried forward unless re-justified. The target SLA is five business days.  
**Policy artifacts/records:** New-role access request; old-role access removal record; role-change HR event  
**Difficulty:** direct  
**Tags:** role-change, partial-offboarding, least-privilege

### QA-094 — §4.3
**Persona:** HR / IT Support  
**Question:** What offboarding timing and account-state evidence is required for a planned departure?  
**Expected answer:** HR creates the departure record as soon as the date is known. IT disables all access no later than the end of the employee’s last working day. The account is disabled immediately but retained for 90 days before deletion so read-only handoff access can be requested if needed.  
**Policy artifacts/records:** HR departure record; account-disablement timestamp; later deletion record  
**Difficulty:** direct  
**Tags:** planned-departure, disablement, 90-days

### QA-095 — §4.4
**Persona:** IT Support  
**Question:** What recurring control should I document to prove missed offboarding steps are caught?  
**Expected answer:** Monthly, reconcile the HR active-employee list against each system’s active-account list. If an account belongs to someone no longer employed, disable it the same day and log the gap for the quarterly access review.  
**Policy artifacts/records:** Monthly reconciliation record; same-day disablement record; quarterly-review issue  
**Difficulty:** direct  
**Tags:** reconciliation, orphan-account, monthly

### QA-096 — §4.5
**Persona:** Hiring manager / IT Support  
**Question:** How should contractor access be documented so it does not become indefinite?  
**Expected answer:** Set an expiration date matching the contracted engagement end date wherever the identity system supports it. An extension requires an explicit renewal before the original expiry. IT reviews time-boxed accounts nearing expiration monthly.  
**Policy artifacts/records:** Contractor access record with expiry; renewal if extended; monthly expiry review  
**Difficulty:** direct  
**Tags:** contractor, time-boxed-access

### QA-097 — §4.6
**Persona:** HR / Security / IT Support  
**Question:** What additional evidence is needed for an involuntary high-risk termination?  
**Expected answer:** Disable access immediately, timed to coincide with the termination conversation. Security reviews the person’s recent access logs and data-export activity for the preceding 30 days. HR, the Engineering Manager, and IT coordinate timing through a dedicated restricted channel.  
**Policy artifacts/records:** Immediate disablement record; 30-day access/export review; restricted coordination record  
**Difficulty:** multi-hop  
**Tags:** high-risk-termination, security-review

### QA-098 — §4.7
**Persona:** IT Support / HR  
**Question:** A former employee is rehired while the old account is still in the 90-day retention window. Can we reactivate it?  
**Expected answer:** No. Provision the person as a new hire with a new account. If the prior account still exists, delete it as part of processing the rehire, while HR links the old and new employment records for traceability.  
**Policy artifacts/records:** New-hire provisioning; deletion of prior account; linked HR employment records  
**Difficulty:** edge-case  
**Tags:** rehire, new-account

### QA-099 — §4.10
**Persona:** IT Support / HR  
**Question:** What should I do if the HR start/departure signal arrives late or is inconsistent?  
**Expected answer:** Escalate the late, missing, or inconsistent HR record to the HR/People Team lead the same business day it is discovered. If there are three or more such cases in a rolling quarter, raise the pattern to the Security Engineer as an audit-relevant finding.  
**Policy artifacts/records:** HR escalation record; quarterly pattern finding if threshold reached  
**Difficulty:** direct  
**Tags:** HR-signal, escalation, systemic-finding

### QA-100 — §4.11; §4.12
**Persona:** IT Support / hiring manager  
**Question:** What non-account artifacts should onboarding/offboarding track for equipment and changing approvers?  
**Expected answer:** Record every issued laptop, mobile device, and hardware token in the asset system and confirm return within five business days of a planned departure; if not returned and no exception exists, open a lost-asset investigation. If a pending access approver is no longer in role, treat the request as blocked and re-route it for a fresh decision; if the new hire’s manager changes before start, the incoming manager must re-confirm existing role-specific requests.  
**Policy artifacts/records:** Asset inventory/return record; lost-asset investigation if needed; re-routed/re-confirmed access requests  
**Difficulty:** multi-hop  
**Tags:** asset-return, approver-change, onboarding


## POL-001 — Software Change Management Policy

### QA-101 — §4.2
**Persona:** Requester  
**Question:** What exact numeric customer-count threshold makes a change high risk?  
**Expected answer:** The policy does not specify a numeric customer-count threshold. The CAB considers customer-base size along with systems affected and access-controlled production impact, using the examples as minimum-conservatism guidance.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-002 — Secure Software Development Lifecycle Policy

### QA-102 — §4.3
**Persona:** QA Engineer  
**Question:** What exact remediation deadline must be used for every medium-severity security finding?  
**Expected answer:** The policy does not set one fixed deadline. Lower-severity findings may be accepted with a documented remediation deadline at the Product Manager’s discretion.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-003 — Code Review and Quality Gate Policy

### QA-103 — §4.1
**Persona:** PR Author  
**Question:** Is 400 lines a hard merge-blocking limit for a pull request?  
**Expected answer:** No. The policy says changes over roughly 400 lines should be split where the change allows; it does not define 400 lines as an automatic merge-blocking threshold.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-004 — Release and Deployment Management Policy

### QA-104 — §4.5
**Persona:** SRE  
**Question:** What exact canary error-rate percentage automatically triggers rollback?  
**Expected answer:** The policy does not specify a numeric canary threshold. It requires pre-configured thresholds where canary analysis is used.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-005 — Incident Management and Response Policy

### QA-105 — §4.2
**Persona:** Incident Commander  
**Question:** What exact revenue-loss amount changes a Sev2 into a Sev1?  
**Expected answer:** The policy does not define monetary thresholds for severity. Severity is based on impact such as widespread outage, confirmed data exposure, or significant degradation.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-006 — Access Control and Least Privilege Policy

### QA-106 — §4.3
**Persona:** Security Engineer  
**Question:** How many days of access-usage history must I pull for every quarterly review?  
**Expected answer:** The policy does not specify a fixed usage-history window. It requires actual usage data where the system supports it and records when attestation is used instead.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-007 — Data Classification and Handling Policy

### QA-107 — §4.3
**Persona:** Data owner  
**Question:** How many years must all Confidential data be retained?  
**Expected answer:** The policy does not specify a universal number of years. It says disposal follows the retention schedule attached to the data’s classification.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-008 — Vendor and Third-Party Risk Management Policy

### QA-108 — §4.1
**Persona:** Security Engineer  
**Question:** What minimum penetration-test score must a Critical vendor achieve?  
**Expected answer:** The policy requires a penetration test summary for Critical vendors but does not define a numeric score or pass threshold.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-009 — Business Continuity and Disaster Recovery Policy

### QA-109 — §4.6
**Persona:** SRE  
**Question:** Does every Tier 1 system have to use a second cloud provider for failover?  
**Expected answer:** No. The policy allows a secondary region with the same provider, a different provider, or a degraded-mode configuration; the plan must document and test the chosen approach and dependencies.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


## POL-010 — IT Onboarding and Offboarding Policy

### QA-110 — §4.11
**Persona:** IT Support  
**Question:** What dollar value should we charge a departing employee for an unreturned laptop?  
**Expected answer:** The policy does not set a charge amount. It requires return tracking and a lost-asset investigation when equipment is not returned and no approved exception applies.  
**Difficulty:** unanswerable-detail  
**Tags:** guardrail, not-specified


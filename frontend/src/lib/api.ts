export function resolveApiBase(env: Record<string, string | undefined>): string {
  return env.VITE_API_BASE ?? "http://localhost:8000";
}

export async function fetchHealth(
  apiBase: string,
  fetchImpl: typeof fetch = fetch,
): Promise<string> {
  const response = await fetchImpl(`${apiBase}/health`);
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  const body = (await response.json()) as { status: string };
  return body.status;
}

export interface Citation {
  document_id: string;
  document_title: string;
}

export interface ChatAnswer {
  answer: string;
  citations: Citation[];
}

export interface PolicyDocument {
  id: string;
  title: string;
  status: "pending" | "embedded" | "failed";
  chunk_count: number | null;
  error: string | null;
}

export async function askChat(
  apiBase: string,
  question: string,
  projectId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ChatAnswer> {
  const response = await fetchImpl(`${apiBase}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, project_id: projectId }),
  });
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as ChatAnswer;
}

export async function uploadDocument(
  apiBase: string,
  file: File,
  fetchImpl: typeof fetch = fetch,
): Promise<PolicyDocument> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetchImpl(`${apiBase}/documents`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as PolicyDocument;
}

export async function listDocuments(
  apiBase: string,
  fetchImpl: typeof fetch = fetch,
): Promise<PolicyDocument[]> {
  return getJson(apiBase, "/documents", fetchImpl);
}

// --- Compliance hierarchy (QA-author editor, ADR-0008) ---

export interface Standard {
  id: string;
  name: string;
  description: string;
}

export interface Clause {
  id: string;
  standard_id: string;
  ordering: number;
  text: string;
}

export type RiskTier = "low" | "medium" | "high";

export interface Requirement {
  id: string;
  clause_id: string;
  description: string;
  risk_tiers: RiskTier[];
  process_step_id: string;
}

// --- Plan navigator: fixed process-step grouping (Q41, V10) ---

export interface ProcessStep {
  id: string;
  title: string;
  ordering: number;
}

export function listProcessSteps(
  apiBase: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ProcessStep[]> {
  return getJson(apiBase, "/process-steps", fetchImpl);
}

async function postJson<T>(
  apiBase: string,
  path: string,
  body: unknown,
  fetchImpl: typeof fetch,
): Promise<T> {
  const response = await fetchImpl(`${apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as T;
}

async function getJson<T>(apiBase: string, path: string, fetchImpl: typeof fetch): Promise<T> {
  const response = await fetchImpl(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export function createStandard(
  apiBase: string,
  name: string,
  description: string,
  fetchImpl: typeof fetch = fetch,
): Promise<Standard> {
  return postJson(apiBase, "/standards", { name, description }, fetchImpl);
}

export function listStandards(apiBase: string, fetchImpl: typeof fetch = fetch): Promise<Standard[]> {
  return getJson(apiBase, "/standards", fetchImpl);
}

export function createClause(
  apiBase: string,
  standardId: string,
  ordering: number,
  text: string,
  fetchImpl: typeof fetch = fetch,
): Promise<Clause> {
  return postJson(apiBase, `/standards/${standardId}/clauses`, { ordering, text }, fetchImpl);
}

export function listClauses(
  apiBase: string,
  standardId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<Clause[]> {
  return getJson(apiBase, `/standards/${standardId}/clauses`, fetchImpl);
}

export function createRequirement(
  apiBase: string,
  clauseId: string,
  description: string,
  riskTiers: RiskTier[],
  fetchImpl: typeof fetch = fetch,
  processStepId?: string,
): Promise<Requirement> {
  return postJson(
    apiBase,
    `/clauses/${clauseId}/requirements`,
    {
      description,
      risk_tiers: riskTiers,
      ...(processStepId ? { process_step_id: processStepId } : {}),
    },
    fetchImpl,
  );
}

export function listRequirements(
  apiBase: string,
  clauseId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<Requirement[]> {
  return getJson(apiBase, `/clauses/${clauseId}/requirements`, fetchImpl);
}

// --- Classification wizard + todo list (S1, S2) ---

export interface WizardAnswers {
  data_sensitivity_high: boolean;
  customer_facing: boolean;
  regulatory_exposure: boolean;
}

export interface AorExtractedFields {
  criticality_tier: string;
  data_classification: string;
  external_dependencies: string[];
  in_house_rationale: string;
}

export interface Project {
  id: string;
  name: string;
  risk_tier: RiskTier | null;
  aor_filename: string | null;
  aor_extracted_fields: AorExtractedFields | null;
}

export type ApprovalState = "not_required" | "not_started" | "submitted" | "approved" | "returned";

export interface TodoItem {
  id: string;
  project_id: string;
  requirement_id: string;
  requirement_description: string;
  clause_text: string;
  standard_name: string;
  status: "pending" | "complied";
  process_step_id: string;
  approval_state: ApprovalState;
  approval_authority: string;
  sla_target: string | null;
  decided_at: string | null;
}

export interface ProjectWithTodos {
  project: Project;
  todos: TodoItem[];
  compliance_percentage: number;
}

export function createProject(
  apiBase: string,
  name: string,
  fetchImpl: typeof fetch = fetch,
): Promise<Project> {
  return postJson(apiBase, "/projects", { name }, fetchImpl);
}

export async function uploadAor(
  apiBase: string,
  projectId: string,
  file: File,
  fetchImpl: typeof fetch = fetch,
): Promise<Project> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetchImpl(`${apiBase}/projects/${projectId}/aor`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as Project;
}

export function classifyProject(
  apiBase: string,
  projectId: string,
  answers: WizardAnswers,
  fetchImpl: typeof fetch = fetch,
): Promise<ProjectWithTodos> {
  return postJson(apiBase, `/projects/${projectId}/classify`, { answers }, fetchImpl);
}

export function listProjects(apiBase: string, fetchImpl: typeof fetch = fetch): Promise<Project[]> {
  return getJson(apiBase, "/projects", fetchImpl);
}

export function getProject(
  apiBase: string,
  projectId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ProjectWithTodos> {
  return getJson(apiBase, `/projects/${projectId}`, fetchImpl);
}

// --- Artifact upload + self-attestation (S3, ADR-0002) ---

export interface Artifact {
  id: string;
  todo_item_id: string;
  filename: string;
}

export interface ArtifactUpload {
  artifact: Artifact;
  todo: TodoItem;
}

export async function uploadArtifact(
  apiBase: string,
  todoId: string,
  file: File,
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactUpload> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetchImpl(`${apiBase}/todos/${todoId}/artifacts`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as ArtifactUpload;
}

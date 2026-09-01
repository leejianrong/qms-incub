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

export async function askChat(
  apiBase: string,
  question: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ChatAnswer> {
  const response = await fetchImpl(`${apiBase}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new Error(`backend returned ${response.status}`);
  }
  return (await response.json()) as ChatAnswer;
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
): Promise<Requirement> {
  return postJson(
    apiBase,
    `/clauses/${clauseId}/requirements`,
    { description, risk_tiers: riskTiers },
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

export interface Project {
  id: string;
  name: string;
  risk_tier: RiskTier;
}

export interface TodoItem {
  id: string;
  project_id: string;
  requirement_id: string;
  requirement_description: string;
  clause_text: string;
  standard_name: string;
  status: "pending" | "complied";
}

export interface ProjectWithTodos {
  project: Project;
  todos: TodoItem[];
}

export function createProject(
  apiBase: string,
  name: string,
  answers: WizardAnswers,
  fetchImpl: typeof fetch = fetch,
): Promise<ProjectWithTodos> {
  return postJson(apiBase, "/projects", { name, answers }, fetchImpl);
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

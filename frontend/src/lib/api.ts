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

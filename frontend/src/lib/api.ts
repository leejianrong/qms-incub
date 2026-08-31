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

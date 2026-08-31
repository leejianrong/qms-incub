<script lang="ts">
  import { resolveApiBase, fetchHealth, askChat, type ChatAnswer } from "./lib/api";

  const apiBase = resolveApiBase(import.meta.env);
  const health = fetchHealth(apiBase);

  let question = $state("");
  let pending = $state(false);
  let result = $state<ChatAnswer | null>(null);
  let error = $state<string | null>(null);

  async function submit() {
    if (!question.trim() || pending) return;
    pending = true;
    error = null;
    result = null;
    try {
      result = await askChat(apiBase, question);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      pending = false;
    }
  }
</script>

<main>
  <h1>QMS Incub</h1>
  <p class="status">
    {#await health}
      Checking backend…
    {:then status}
      Backend health: <strong>{status}</strong>
    {:catch err}
      Backend unreachable: {err.message}
    {/await}
  </p>

  <section class="chat">
    <h2>Ask the policy chatbot</h2>
    <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
      <input
        type="text"
        bind:value={question}
        placeholder="e.g. Who is the approving authority for this policy?"
        disabled={pending}
      />
      <button type="submit" disabled={pending || !question.trim()}>
        {pending ? "Asking…" : "Ask"}
      </button>
    </form>

    {#if error}
      <p class="error">Error: {error}</p>
    {/if}

    {#if result}
      <div class="answer">
        <p>{result.answer}</p>
        {#if result.citations.length > 0}
          <ul class="citations">
            {#each result.citations as citation (citation.document_id)}
              <li>{citation.document_title}</li>
            {/each}
          </ul>
        {/if}
      </div>
    {/if}
  </section>
</main>

<style>
  main {
    font-family: system-ui, sans-serif;
    max-width: 32rem;
    margin: 4rem auto;
    padding: 0 1rem;
  }

  .status {
    color: #64748b;
    font-size: 0.9rem;
  }

  .chat {
    margin-top: 2rem;
  }

  form {
    display: flex;
    gap: 0.5rem;
  }

  input {
    flex: 1;
    padding: 0.5rem;
  }

  button {
    padding: 0.5rem 1rem;
  }

  .error {
    color: #b91c1c;
  }

  .answer {
    margin-top: 1rem;
    padding: 1rem;
    border: 1px solid #cbd5e1;
    border-radius: 0.5rem;
  }

  .citations {
    margin: 0.5rem 0 0;
    padding-left: 1.25rem;
    font-size: 0.85rem;
    color: #475569;
  }
</style>

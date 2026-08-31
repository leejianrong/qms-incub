<script lang="ts">
  import { fetchDocuments, startBatch, type PolicyDocumentStatus } from "./api";

  let { apiBase }: { apiBase: string } = $props();

  let count = $state(5);
  let seed = $state(0);
  let starting = $state(false);
  let startError = $state<string | null>(null);
  let documents = $state<PolicyDocumentStatus[]>([]);
  let loadError = $state<string | null>(null);

  async function refresh() {
    try {
      documents = await fetchDocuments(apiBase);
      loadError = null;
    } catch (err) {
      loadError = err instanceof Error ? err.message : String(err);
    }
  }

  async function generate() {
    if (starting) return;
    starting = true;
    startError = null;
    try {
      await startBatch(apiBase, { count, seed });
      await refresh();
    } catch (err) {
      startError = err instanceof Error ? err.message : String(err);
    } finally {
      starting = false;
    }
  }

  // Poll while anything is still pending; a manual Refresh button covers
  // the rest. No infra beyond setInterval — fine for V5's spike scope.
  $effect(() => {
    const hasPending = documents.some((d) => d.status === "pending");
    if (!hasPending) return;
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  });

  refresh();
</script>

<section class="dashboard">
  <h2>Generate synthetic variants</h2>
  <form onsubmit={(e) => { e.preventDefault(); generate(); }}>
    <label>
      Count
      <input type="number" min="1" max="100" bind:value={count} disabled={starting} />
    </label>
    <label>
      Seed
      <input type="number" bind:value={seed} disabled={starting} />
    </label>
    <button type="submit" disabled={starting}>
      {starting ? "Starting…" : "Generate"}
    </button>
    <button type="button" onclick={refresh}>Refresh</button>
  </form>

  {#if startError}
    <p class="error">Error: {startError}</p>
  {/if}
  {#if loadError}
    <p class="error">Error loading documents: {loadError}</p>
  {/if}

  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Origin</th>
        <th>Status</th>
        <th>Chunks</th>
      </tr>
    </thead>
    <tbody>
      {#each documents as doc (doc.id)}
        <tr>
          <td>{doc.title}</td>
          <td>{doc.is_synthetic ? "synthetic" : doc.origin}</td>
          <td><span class="status status-{doc.status}">{doc.status}</span></td>
          <td>{doc.chunk_count ?? "—"}</td>
        </tr>
        {#if doc.error}
          <tr class="error-row">
            <td colspan="4">{doc.error}</td>
          </tr>
        {/if}
      {:else}
        <tr>
          <td colspan="4">No documents yet.</td>
        </tr>
      {/each}
    </tbody>
  </table>
</section>

<style>
  .dashboard {
    margin-top: 2rem;
  }

  form {
    display: flex;
    align-items: end;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  label {
    display: flex;
    flex-direction: column;
    font-size: 0.8rem;
    color: #475569;
    gap: 0.25rem;
  }

  input {
    width: 5rem;
    padding: 0.4rem;
  }

  button {
    padding: 0.5rem 1rem;
  }

  .error {
    color: #b91c1c;
  }

  table {
    margin-top: 1rem;
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  th,
  td {
    text-align: left;
    padding: 0.4rem 0.5rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .status {
    padding: 0.1rem 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
  }

  .status-embedded {
    background: #dcfce7;
    color: #166534;
  }

  .status-pending {
    background: #fef9c3;
    color: #854d0e;
  }

  .status-failed {
    background: #fee2e2;
    color: #991b1b;
  }

  .error-row {
    color: #b91c1c;
    font-size: 0.8rem;
  }
</style>

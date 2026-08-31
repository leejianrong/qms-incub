<script lang="ts">
  import { resolveApiBase, fetchHealth } from "./lib/api";

  const apiBase = resolveApiBase(import.meta.env);
  const health = fetchHealth(apiBase);
</script>

<main>
  <h1>QMS Incub</h1>
  <p>Walking skeleton — this page just proves the frontend can reach the backend.</p>

  {#await health}
    <p>Checking backend…</p>
  {:then status}
    <p>Backend health: <strong>{status}</strong></p>
  {:catch error}
    <p>Backend unreachable: {error.message}</p>
  {/await}
</main>

<style>
  main {
    font-family: system-ui, sans-serif;
    max-width: 32rem;
    margin: 4rem auto;
    padding: 0 1rem;
  }
</style>

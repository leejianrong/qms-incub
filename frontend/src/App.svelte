<script lang="ts">
  import {
    resolveApiBase,
    fetchHealth,
    askChat,
    listDocuments,
    uploadDocument,
    type ChatAnswer,
    type PolicyDocument,
  } from "./lib/api";

  const apiBase = resolveApiBase(import.meta.env);
  const health = fetchHealth(apiBase);

  let question = $state("");
  let pending = $state(false);
  let result = $state<ChatAnswer | null>(null);
  let error = $state<string | null>(null);
  let documents = $state<PolicyDocument[]>([]);
  let documentError = $state<string | null>(null);
  let uploading = $state(false);

  async function loadDocuments() {
    try {
      documents = await listDocuments(apiBase);
    } catch (err) {
      documentError = err instanceof Error ? err.message : String(err);
    }
  }

  loadDocuments();

  async function upload(fileList: FileList | null, input: HTMLInputElement) {
    const file = fileList?.[0];
    if (!file || uploading) return;
    uploading = true;
    documentError = null;
    try {
      const document = await uploadDocument(apiBase, file);
      documents = [document, ...documents.filter((item) => item.id !== document.id)];
      input.value = "";
    } catch (err) {
      documentError = err instanceof Error ? err.message : String(err);
    } finally {
      uploading = false;
    }
  }

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

  <section class="documents" aria-labelledby="document-upload-heading">
    <h2 id="document-upload-heading">Policy documents</h2>
    <p>Upload a PDF to add it to the policy corpus used by the chatbot.</p>
    <label class="upload-control">
      <span>{uploading ? "Ingesting PDF…" : "Choose policy PDF"}</span>
      <input
        type="file"
        accept="application/pdf,.pdf"
        disabled={uploading}
        onchange={(event) => upload((event.target as HTMLInputElement).files, event.target as HTMLInputElement)}
      />
    </label>
    {#if documentError}
      <p class="error">Upload error: {documentError}</p>
    {/if}
    {#if documents.length > 0}
      <ul class="document-list">
        {#each documents as document (document.id)}
          <li>
            <strong>{document.title}</strong>
            <span>{document.status}{document.chunk_count !== null ? ` · ${document.chunk_count} chunks` : ""}</span>
            {#if document.error}<small>{document.error}</small>{/if}
          </li>
        {/each}
      </ul>
    {:else}
      <p class="empty">No policy documents uploaded yet.</p>
    {/if}
  </section>
</main>

<style>
  main {
    font-family: system-ui, sans-serif;
    max-width: 40rem;
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

  .documents {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #cbd5e1;
  }

  .documents > p {
    color: #475569;
  }

  .upload-control {
    display: inline-flex;
    margin-top: 0.5rem;
    padding: 0.5rem 1rem;
    color: white;
    background: #4d2df0;
    border-radius: 0.375rem;
    cursor: pointer;
  }

  .upload-control:has(input:disabled) {
    opacity: 0.65;
    cursor: wait;
  }

  .upload-control input {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
  }

  .document-list {
    padding: 0;
    list-style: none;
  }

  .document-list li {
    display: grid;
    gap: 0.2rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid #e2e8f0;
  }

  .document-list span, .document-list small, .empty {
    color: #64748b;
    font-size: 0.85rem;
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

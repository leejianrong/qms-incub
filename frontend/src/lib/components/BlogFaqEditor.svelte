<script lang="ts">
  import {
    createBlogPost, createFAQEntry, listBlogPosts, listFAQEntries, publishBlogPost,
    publishFAQEntry, resolveApiBase, updateBlogPost, updateFAQEntry,
    type BlogPost, type FAQEntry,
  } from "$lib/api";

  const apiBase = resolveApiBase(import.meta.env);
  let blogs = $state<BlogPost[]>([]);
  let faqs = $state<FAQEntry[]>([]);
  let blogTitle = $state("");
  let blogBody = $state("");
  let faqQuestion = $state("");
  let faqAnswer = $state("");
  let editingBlog = $state<string | null>(null);
  let editingFaq = $state<string | null>(null);
  let saving = $state(false);
  let error = $state<string | null>(null);

  async function load() {
    try { [blogs, faqs] = await Promise.all([listBlogPosts(apiBase), listFAQEntries(apiBase)]); }
    catch (err) { error = err instanceof Error ? err.message : String(err); }
  }
  load();

  function editBlog(post: BlogPost) { editingBlog = post.id; blogTitle = post.title; blogBody = post.body; }
  function editFaq(entry: FAQEntry) { editingFaq = entry.id; faqQuestion = entry.question; faqAnswer = entry.answer; }
  function resetBlog() { editingBlog = null; blogTitle = ""; blogBody = ""; }
  function resetFaq() { editingFaq = null; faqQuestion = ""; faqAnswer = ""; }

  async function saveBlog() {
    if (saving) return; saving = true; error = null;
    try {
      if (editingBlog) await updateBlogPost(apiBase, editingBlog, blogTitle, blogBody);
      else await createBlogPost(apiBase, blogTitle, blogBody);
      resetBlog(); await load();
    }
    catch (err) { error = err instanceof Error ? err.message : String(err); } finally { saving = false; }
  }
  async function saveFaq() {
    if (saving) return; saving = true; error = null;
    try {
      if (editingFaq) await updateFAQEntry(apiBase, editingFaq, faqQuestion, faqAnswer);
      else await createFAQEntry(apiBase, faqQuestion, faqAnswer);
      resetFaq(); await load();
    }
    catch (err) { error = err instanceof Error ? err.message : String(err); } finally { saving = false; }
  }
  async function publish(kind: "blog" | "faq", id: string) {
    if (saving) return; saving = true; error = null;
    try {
      if (kind === "blog") await publishBlogPost(apiBase, id);
      else await publishFAQEntry(apiBase, id);
      await load();
    }
    catch (err) { error = err instanceof Error ? err.message : String(err); } finally { saving = false; }
  }
</script>

<main>
  <header><h1>Blog &amp; FAQ</h1><p>Plain-text admin content. Publishing makes it available to the policy chatbot.</p></header>
  {#if error}<p class="error">{error}</p>{/if}
  <section>
    <h2>{editingBlog ? "Edit blog post" : "New blog post"}</h2>
    <input aria-label="Blog title" bind:value={blogTitle} placeholder="Post title" />
    <textarea aria-label="Blog body" bind:value={blogBody} placeholder="Write the post in plain text"></textarea>
    <button onclick={saveBlog} disabled={saving}>{editingBlog ? "Save changes" : "Save draft"}</button>
    {#if editingBlog}<button class="secondary" onclick={resetBlog}>Cancel</button>{/if}
    <ul>{#each blogs as blog (blog.id)}<li><strong>{blog.title || "Untitled draft"}</strong><span>{blog.published_at ? `Published · ${blog.chunk_count ?? 0} chunks` : "Draft"}</span><div><button class="secondary" onclick={() => editBlog(blog)}>Edit</button><button onclick={() => publish("blog", blog.id)} disabled={saving}>Publish</button></div></li>{:else}<li class="empty">No blog posts yet.</li>{/each}</ul>
  </section>
  <section>
    <h2>{editingFaq ? "Edit FAQ entry" : "New FAQ entry"}</h2>
    <input aria-label="FAQ question" bind:value={faqQuestion} placeholder="Question" />
    <textarea aria-label="FAQ answer" bind:value={faqAnswer} placeholder="Answer in plain text"></textarea>
    <button onclick={saveFaq} disabled={saving}>{editingFaq ? "Save changes" : "Save draft"}</button>
    {#if editingFaq}<button class="secondary" onclick={resetFaq}>Cancel</button>{/if}
    <ul>{#each faqs as faq (faq.id)}<li><strong>{faq.question || "Untitled FAQ draft"}</strong><span>{faq.published_at ? `Published · ${faq.chunk_count ?? 0} chunks` : "Draft"}</span><div><button class="secondary" onclick={() => editFaq(faq)}>Edit</button><button onclick={() => publish("faq", faq.id)} disabled={saving}>Publish</button></div></li>{:else}<li class="empty">No FAQ entries yet.</li>{/each}</ul>
  </section>
</main>

<style>
  main { font-family: system-ui, sans-serif; max-width: 48rem; margin: 3rem auto; padding: 0 1rem; }
  header p, span, .empty { color: #64748b; } section { margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #cbd5e1; }
  input, textarea { box-sizing: border-box; display: block; width: 100%; margin: .65rem 0; padding: .65rem; font: inherit; } textarea { min-height: 7rem; resize: vertical; }
  button { margin: .25rem .4rem .25rem 0; padding: .45rem .8rem; background: #4d2df0; border: 0; border-radius: .3rem; color: white; cursor: pointer; } .secondary { background: #e2e8f0; color: #1e293b; }
  ul { padding: 0; list-style: none; } li { display: grid; grid-template-columns: 1fr auto; gap: .25rem 1rem; padding: .8rem 0; border-bottom: 1px solid #e2e8f0; } li div { grid-column: 1 / -1; } .error { color: #b91c1c; }
</style>

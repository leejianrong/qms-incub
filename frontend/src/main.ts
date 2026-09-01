import { mount, type Component } from 'svelte'
import './app.css'
import App from './App.svelte'
import Showcase from './lib/components/Showcase.svelte'
import StandardEditor from './lib/components/StandardEditor.svelte'
import Console from './lib/components/Console.svelte'
import BlogFaqEditor from './lib/components/BlogFaqEditor.svelte'

// V13: Console.svelte is the real console shell — it owns the core PM
// workflow (dashboard / wizard / project detail) and does its own
// client-side routing between those three via lib/router.svelte.ts, so
// they all mount the same component here and never trigger a full page
// reload when navigating between them. QA-author tools
// (showcase/editor/content) and the standalone document-upload utility
// are separate personas outside this slice's scope, so they keep the
// simple one-shot pathname-keyed mount this file always used.
const routes: Record<string, Component> = {
  '/showcase': Showcase,
  '/editor': StandardEditor,
  '/wizard': Console,
  '/project': Console,
  '/content': BlogFaqEditor,
  '/documents': App,
}

const app = mount(routes[window.location.pathname] ?? Console, {
  target: document.getElementById('app')!,
})

export default app

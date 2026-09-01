import { mount, type Component } from 'svelte'
import './app.css'
import App from './App.svelte'
import Showcase from './lib/components/Showcase.svelte'
import StandardEditor from './lib/components/StandardEditor.svelte'
import Wizard from './lib/components/Wizard.svelte'
import ProjectDashboard from './lib/components/ProjectDashboard.svelte'
import BlogFaqEditor from './lib/components/BlogFaqEditor.svelte'

// No router library yet (V2) — a handful of pathname-keyed routes is
// enough until V13 replaces this with the real console shell.
const routes: Record<string, Component> = {
  '/showcase': Showcase,
  '/editor': StandardEditor,
  '/wizard': Wizard,
  '/project': ProjectDashboard,
  '/content': BlogFaqEditor,
}

const app = mount(routes[window.location.pathname] ?? App, {
  target: document.getElementById('app')!,
})

export default app

import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'
import Showcase from './lib/components/Showcase.svelte'

const isShowcaseRoute = window.location.pathname === '/showcase'

const app = mount(isShowcaseRoute ? Showcase : App, {
  target: document.getElementById('app')!,
})

export default app

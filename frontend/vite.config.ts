import path from 'node:path'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: {
      $lib: path.resolve(import.meta.dirname, './src/lib'),
    },
  },
  server: {
    // Backend CORS is hardcoded to http://localhost:5173 (see
    // backend/src/qms_incub/main.py) with no equivalent fallback wiring
    // for the frontend's port. Without strictPort, Vite silently moves to
    // 5174 when 5173 is taken and every API call breaks with a CORS error
    // that doesn't obviously point back here — fail loudly instead.
    port: 5173,
    strictPort: true,
    // Bind all interfaces, not just localhost — inside the `frontend`
    // container (ADR-0017) the nginx `proxy` service reaches this by its
    // Docker-network hostname, which only works if Vite listens on more
    // than the container's own loopback. Harmless for host-based dev too.
    host: true,
  },
})

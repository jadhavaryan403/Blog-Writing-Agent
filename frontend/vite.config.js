import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The built app is served by FastAPI from frontend/dist at the site root,
// so the default base of '/' is correct. The dev server proxies API calls
// to the local backend.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});

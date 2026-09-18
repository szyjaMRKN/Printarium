/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Backend jest osobnym procesem — w developmencie proxy przekazuje /api na port 8000.
//
// VITE_BASE_PATH pozwala zbudować aplikację do podkatalogu domeny
// (np. VITE_BASE_PATH=/ewidencja/ dla adresu mojadomena.pl/ewidencja).
// Adresy API, routing i service worker liczone są od tej wartości.
const basePath = normalizeBase(process.env.VITE_BASE_PATH);

function normalizeBase(value: string | undefined): string {
  if (!value) return '/';
  const withLeading = value.startsWith('/') ? value : `/${value}`;
  return withLeading.endsWith('/') ? withLeading : `${withLeading}/`;
}

export default defineConfig({
  base: basePath,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
      '/health': {
        target: process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
  // `npm run preview` służy do sprawdzenia builda produkcyjnego lokalnie.
  preview: {
    port: 4173,
    proxy: {
      '/api': { target: process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8000', changeOrigin: false },
      '/health': { target: process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        // Biblioteka wykresów jest największą zależnością — trzymamy ją w osobnej paczce,
        // żeby powłoka aplikacji ładowała się szybciej.
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});

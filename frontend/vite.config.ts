import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The dev server binds 0.0.0.0 and accepts any host header so it works
// behind the sandbox preview proxy.  All API and WebSocket traffic is
// proxied to the FastAPI backend on :8000, so the browser only ever talks
// to its own origin (relative URLs, no hardcoded localhost).
export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        manualChunks: {
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          plotly: ['plotly.js-dist-min'],
          react: ['react', 'react-dom', 'react-router-dom', 'zustand'],
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
});

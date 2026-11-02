import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          query: ['@tanstack/react-query'],
          state: ['zustand'],
          dates: ['date-fns', 'react-datepicker'],
        },
      },
    },
    chunkSizeWarningLimit: 300,
  },
  server: {
    port: 5173,
    proxy: {
      // Ledger engine + auth live in the gateway; route them before the
      // catch-all /api proxy below (object order matters in Vite).
      '/api/ledger': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:3001',
        changeOrigin: true,
        ws: true,
      },
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});

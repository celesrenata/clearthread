import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Vite options tailored for Tauri development
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  // Tauri expects an absolute path
  build: {
    outDir: 'dist',
    target: process.env.TAURI_PLATFORM === 'windows' ? 'chrome70' : 'es2021',
    emptyOutDir: true,
  },
});

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      'alumnos.felipe-villa-nueva-teotitlan.site',
      'aulas.felipe-villa-nueva-teotitlan.site',
      'extras.felipe-villa-nueva-teotitlan.site',
      '.felipe-villa-nueva-teotitlan.site',
    ],
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    globals: true,
    css: true,
    exclude: ['**/node_modules/**', '**/e2e/**', '**/dist/**']
  }
});

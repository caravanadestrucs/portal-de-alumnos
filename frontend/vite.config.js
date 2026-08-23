import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // TODO: gate behind VITE_ALLOWED_HOSTS env
    allowedHosts: [
      'alumnos.felipe-villa-nueva-teotitlan.site'
    ]
  }
});

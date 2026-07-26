import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Handle SPA routing - redirect all requests to index.html
    historyApiFallback: true,
    hmr: {
      // Only update changed modules, don't do full reload on error
      overlay: false,
    },
  },
  // Ensure proper base path
  base: '/',
})

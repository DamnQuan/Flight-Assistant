import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api_web': 'http://backend:5000',
      '/api/v1': 'http://backend:5000'
    }
  },
  build: {
    outDir: '../static/dist'
  }
})

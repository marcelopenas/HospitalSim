import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true, rewrite: path => path.replace(/^\/api/, '') } } },
  preview: { proxy: { '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true, rewrite: path => path.replace(/^\/api/, '') } } },
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
})

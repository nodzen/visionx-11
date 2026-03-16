import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    https: {
      key: fs.readFileSync(path.resolve(__dirname, '../key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, '../cert.pem')),
    },
    proxy: {
      '/api': {
        target: 'https://127.0.0.1:8000',
        secure: false,
        changeOrigin: true,
        ws: true
      }
    }
  }
})

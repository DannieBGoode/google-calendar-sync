import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": new URL("./src", import.meta.url).pathname },
  },
  server: {
    proxy: { "/api": "http://localhost:8000", "/health": "http://localhost:8000" },
  },
  build: {
    outDir: "../src/calendar_sync/interfaces/api/static",
    emptyOutDir: true,
  },
})

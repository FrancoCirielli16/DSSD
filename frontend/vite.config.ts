import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Compila todas las islas a un único bundle con nombre fijo dentro de los estáticos de FastAPI:
// lo sirve el mismo servidor que las páginas Jinja (mismo origen: sin CORS ni tokens).
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../backend/app/static/islands",
    emptyOutDir: true,
    rolldownOptions: {
      input: "src/main.tsx",
      output: {
        entryFileNames: "islands.js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "islands[extname]",
      },
    },
  },
  test: {
    environment: "jsdom",
  },
});

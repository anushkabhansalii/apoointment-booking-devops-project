import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the Vite server proxies /api to the local FastAPI backend,
// mirroring what Nginx (Docker) and the Ingress (Kubernetes) do in production.
export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(process.env.VITE_APP_VERSION || "dev"),
  },
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.VITE_API_PROXY || "http://localhost:8000",
    },
  },
  build: { outDir: "dist", sourcemap: false },
});

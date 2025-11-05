import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Configuración de desarrollo de Vite con Flask
export default defineConfig({
  base: '/app_estudiante/',
  
  plugins: [react()],
  server: {
    port: 5173, // Puerto del frontend
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000", // Tu backend Flask
        changeOrigin: true,
        secure: false,
        credentials: "include", // Permitir envío de cookies
      },
      "/login": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        secure: false,
        credentials: "include",
      },
    },
    cors: {
      origin: ["http://127.0.0.1:5173"], // Solo React
      credentials: true, // Permitir cookies
    },
  },
});

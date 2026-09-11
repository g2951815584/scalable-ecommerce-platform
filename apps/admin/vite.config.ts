import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/admin/",
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          antd: ["antd", "@ant-design/icons"],
        },
      },
    },
  },
  server: {
    port: 5174,
    host: "0.0.0.0",
    proxy: {
      "/api/v1/auth": "http://127.0.0.1:8001",
      "/api/v1/users": "http://127.0.0.1:8001",
      "/api/v1/roles": "http://127.0.0.1:8001",
      "/api/v1/permissions": "http://127.0.0.1:8001",
      "/api/v1/categories": "http://127.0.0.1:8002",
      "/api/v1/products": "http://127.0.0.1:8002",
      "/api/v1/admin": "http://127.0.0.1:8002",
      "/api/v1/orders": "http://127.0.0.1:8004",
      "/api/v1/payments": "http://127.0.0.1:8005",
      "/api/v1/notifications": "http://127.0.0.1:8006",
    },
  },
});

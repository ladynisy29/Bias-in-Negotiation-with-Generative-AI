const { resolve } = require("path");
const { defineConfig } = require("vite");

module.exports = defineConfig({
  server: {
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        onboarding: resolve(__dirname, "src/pages/Onboarding.html"),
        chat: resolve(__dirname, "src/pages/Chat.html"),
        results: resolve(__dirname, "src/pages/Results.html"),
        login: resolve(__dirname, "src/pages/login.html"),
        register: resolve(__dirname, "src/pages/register.html"),
        startSession: resolve(__dirname, "src/pages/start-session.html"),
        baseLayout: resolve(__dirname, "src/pages/BaseLayout.html"),
      },
    },
  },
});

import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  // Relative paths so the build runs from any folder or host (Vercel, a test link, a phone).
  base: './',
  build: {
    target: 'es2022', // top-level await while the models load
    chunkSizeWarningLimit: 900,
  },
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: false, // registered in src/main.js so a failure never stops the game
      includeAssets: ['icons/*.png'],
      manifest: {
        name: 'Behind the Sky (prototype)',
        short_name: 'Behind the Sky',
        description: 'Gray-box prototype: fight, spend spirit power, pay it back at the crossroads.',
        start_url: '.',
        scope: '.',
        display: 'fullscreen',
        orientation: 'landscape',
        background_color: '#121a14',
        theme_color: '#121a14',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,png,webmanifest,glb}'],
        cleanupOutdatedCaches: true,
      },
    }),
  ],
  test: {
    include: ['tests/**/*.test.js'],
  },
});

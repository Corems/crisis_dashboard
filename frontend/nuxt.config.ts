export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  ssr: true,
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss', '@vite-pwa/nuxt'],

  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      id: '/crisismeter',
      name: 'Crisis Dashboard',
      short_name: 'Crisis',
      description: 'Macroeconomic crisis monitoring dashboard',
      start_url: '/',
      theme_color: '#111827',
      background_color: '#111827',
      display: 'standalone',
      orientation: 'portrait',
      lang: 'uk',
      categories: ['finance', 'productivity'],
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
        { src: '/icon-192-maskable.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      ],
    },
    workbox: {
      navigateFallback: null,
      navigationPreload: true,
      skipWaiting: true,
      clientsClaim: true,
      globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
      runtimeCaching: [
        {
          urlPattern: ({request}) => request.mode === 'navigate',
          handler: 'NetworkFirst',
          options: {
            cacheName: 'pages-cache',
            networkTimeoutSeconds: 3,
          },
        },
        {
          urlPattern: /\/api\/.*/,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            expiration: { maxAgeSeconds: 60 * 60 * 24 },
            networkTimeoutSeconds: 3,
          },
        },
      ],
    },
  },
  pages: true,
  runtimeConfig: {
    apiUrl: process.env.API_URL || 'http://127.0.0.1',
    public: {
      cloudflareWorkerUrl: process.env.CLOUDFLARE_WORKER_URL || 'https://youtube-transcript-proxy.YOUR_SUBDOMAIN.workers.dev',
      supadataApiKey: process.env.SUPADATA_API_KEY || ''
    }
  },
  nitro: {
    routeRules: {
      '/api/**': { proxy: 'http://127.0.0.1:8000/**' }
    }
  }
})

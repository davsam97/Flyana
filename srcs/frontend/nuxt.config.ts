import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  app: {
    head: {
      link: [
        // SVG first: browsers that support it prefer it over the .ico below,
        // which stays as the fallback favicon.ico convention expects. Both are
        // `rel="icon"`, not the legacy `alternate icon`: declaring the type is
        // what makes a browser skip the SVG it cannot read, and `alternate
        // icon` is not a value the spec — nor Nuxt's `rel` type — allows.
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'icon', href: '/favicon.ico', sizes: '16x16 32x32 48x48 64x64' },
      ],
      meta: [
        // Tints the browser chrome (Safari, Chrome/Edge on mobile) to the page
        { name: 'theme-color', content: '#041010' },
        // iOS Safari otherwise turns digit runs (room codes, scores) into tel: links
        { name: 'format-detection', content: 'telephone=no' },
      ],
      // Classic, blocking, ES5: shows a message instead of a blank page on a
      // browser below the floor in `vite.build.target`
      script: [{ src: '/browser-check.js' }],
      noscript: [{ textContent: 'Flyana needs JavaScript. / Flyana a besoin de JavaScript.' }],
    },
  },

  css: [
    '@fontsource-variable/ibm-plex-sans/wght.css',
    '@fontsource/ibm-plex-mono/latin-400.css',
    '@fontsource/ibm-plex-mono/latin-500.css',
    '@fontsource/ibm-plex-mono/latin-600.css',
    // Formula typesetting for the course; its fonts are bundled, no CDN
    'katex/dist/katex.min.css',
    '~/assets/css/main.css',
  ],
  ssr: false,
  vite: {
    plugins: [tailwindcss()],
    // Supported browsers, documented in the README. Same floor as Tailwind CSS
    // v4 (@property, color-mix, cascade layers): newer JS syntax is lowered to
    // it, so Firefox, Edge and Safari run the same bundle as Chrome.
    build: {
      target: ['chrome111', 'edge111', 'firefox128', 'safari16.4'],
    },
  },
  modules: ['@nuxt/icon', '@nuxtjs/color-mode', '@nuxt/eslint', '@nuxtjs/i18n'],
  // SPA build: no Nitro server to serve icons, and the CSP forbids the Iconify
  // API. Every `lucide:*` name found in the sources ships in the client bundle.
  icon: {
    clientBundle: {
      scan: true,
      // Named in TypeScript (utils/course.ts), which the scan does not read
      icons: [
        'lucide:wind',
        'lucide:plane',
        'lucide:flame',
        'lucide:orbit',
        'lucide:satellite',
        'lucide:cpu',
        'lucide:landmark',
        'lucide:book-open',
      ],
    },
  },
  colorMode: {
    preference: 'dark',
    fallback: 'dark',
    dataValue: 'theme',
    classSuffix: '',
  },
  i18n: {
    defaultLocale: 'fr',
    strategy: 'no_prefix',
    locales: [
      { code: 'fr', name: 'Français', language: 'fr-FR', file: 'fr.json' },
      { code: 'en', name: 'English', language: 'en-US', file: 'en.json' },
    ],
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'flyana_locale',
      alwaysRedirect: true,
      fallbackLocale: 'fr',
    },
  },
})

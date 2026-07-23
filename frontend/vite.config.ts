// frontend/vite.config.ts
import path from 'path'
import { fileURLToPath } from 'url'

import { sentryVitePlugin } from '@sentry/vite-plugin'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  build: {
    // Source maps for Sentry — uploaded in CI when SENTRY_AUTH_TOKEN is set.
    sourcemap: true,
  },
  plugins: [
    react(),
    tailwindcss(),
    ...(process.env.SENTRY_AUTH_TOKEN
      ? [
          sentryVitePlugin({
            org: process.env.SENTRY_ORG,
            project: process.env.SENTRY_PROJECT,
            authToken: process.env.SENTRY_AUTH_TOKEN,
            release: {
              name: process.env.VITE_SENTRY_RELEASE,
            },
            sourcemaps: {
              assets: './dist/assets/**',
              filesToDeleteAfterUpload: ['./dist/assets/**/*.map'],
            },
          }),
        ]
      : []),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})

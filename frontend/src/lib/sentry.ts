// frontend/src/lib/sentry.ts
import * as Sentry from '@sentry/react';
import { optionalViteEnv } from '@/lib/env';

function getSentryDsn(): string | undefined {
  return optionalViteEnv('VITE_SENTRY_DSN');
}

function isSentryScreenshotEnabled(): boolean {
  const raw = optionalViteEnv('VITE_SENTRY_ENABLE_SCREENSHOT');
  return raw ? raw.toLowerCase() !== 'false' : false;
}

export function initSentry(): void {
  const dsn = getSentryDsn();
  if (!dsn) return;

  const environment = import.meta.env.MODE;
  const release = optionalViteEnv('VITE_SENTRY_RELEASE');
  const sendDefaultPii =
    (optionalViteEnv('VITE_SENTRY_SEND_DEFAULT_PII') ?? '').toLowerCase() === 'true';

  Sentry.init({
    dsn,
    environment,
    release,
    sendDefaultPii,
    _experiments: {
      enableLogs: true,
    },
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
        networkDetailAllowUrls: [],
      }),
      Sentry.feedbackIntegration({
        autoInject: false,
        colorScheme: 'system',
        enableScreenshot: isSentryScreenshotEnabled(),
        showBranding: false,
        useSentryUser: {
          email: 'email',
          name: 'name',
        },
        themeLight: {
          background: '#FFFFFF',
          backgroundHover: '#F1F5F9',
          foreground: '#334155',
          border: '1px solid #E2E8F0',
          boxShadow: '0 4px 12px rgb(15 23 42 / 0.08)',
          submitBackground: '#0F172A',
          submitBackgroundHover: '#334155',
          submitForeground: '#FFFFFF',
          inputBackground: '#FFFFFF',
          inputForeground: '#334155',
          inputBorder: '1px solid #94A3B8',
          inputOutlineFocus: '#4F46E5',
        },
        themeDark: {
          background: '#0F172A',
          backgroundHover: '#1E293B',
          foreground: '#CBD5E1',
          border: '1px solid #1E293B',
          boxShadow: '0 4px 12px rgb(0 0 0 / 0.32)',
          submitBackground: '#F8FAFC',
          submitBackgroundHover: '#E2E8F0',
          submitForeground: '#020617',
          inputBackground: '#1E293B',
          inputForeground: '#CBD5E1',
          inputBorder: '1px solid #64748B',
          inputOutlineFocus: '#818CF8',
        },
      }),
    ],
    tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
    replaysSessionSampleRate: environment === 'production' ? 0.1 : 1.0,
    replaysOnErrorSampleRate: 1.0,
  });
}

export { Sentry };

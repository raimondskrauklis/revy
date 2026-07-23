// frontend/src/lib/log.ts
/**
 * Structured logging — dev console + Sentry Logs when DSN is configured.
 * See docs/errors/OBSERVABILITY.md
 */
import * as Sentry from '@sentry/react';

type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';

type LogAttributes = Record<string, string | number | boolean | null | undefined>;

function createLog(level: LogLevel) {
  return (message: string, attributes?: LogAttributes) => {
    if (import.meta.env.DEV) {
      const consoleMethod =
        level === 'trace' ? 'debug' : level === 'fatal' ? 'error' : level;
      console[consoleMethod](`[${level.toUpperCase()}]`, message, attributes ?? '');
    }

    const logger = Sentry.logger;
    if (logger && typeof logger[level] === 'function') {
      try {
        logger[level](message, attributes);
      } catch {
        // Sentry not initialized — no-op in production
      }
    }
  };
}

export const log = {
  trace: createLog('trace'),
  debug: createLog('debug'),
  info: createLog('info'),
  warn: createLog('warn'),
  error: createLog('error'),
  fatal: createLog('fatal'),
} as const;

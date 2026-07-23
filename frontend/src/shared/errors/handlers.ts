// frontend/src/shared/errors/handlers.ts
import type { ErrorContext } from './types';
import { mapApiError } from './errorMapper';
import { showDomainErrorToast } from './toasts';

let config: { login?: () => void; unauthorizedPath?: string } = {};

export function configureErrorHandling(next: typeof config) {
  config = next;
}

function isCanceled(error: unknown): boolean {
  if (typeof error !== 'object' || error === null) return false;
  const name = (error as { name?: unknown }).name;
  return name === 'CanceledError' || name === 'AbortError';
}

export function handleError(error: unknown, context?: ErrorContext) {
  if (isCanceled(error)) return;
  const domainError = mapApiError(error, context);

  if (domainError.statusCode === 401 && config.login) {
    config.login();
    return;
  }

  if (
    domainError.statusCode === 403
    && config.unauthorizedPath
    && !context?.domain
  ) {
    window.location.href = config.unauthorizedPath;
    return;
  }

  showDomainErrorToast(domainError);
}

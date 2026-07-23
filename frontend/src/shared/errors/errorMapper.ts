// frontend/src/shared/errors/errorMapper.ts
import { AxiosError } from 'axios';
import type { DomainError, ErrorContext, FlatApiErrorResponse } from './types';

type ParsedApiError = Pick<FlatApiErrorResponse, 'error' | 'message' | 'details' | 'field'>;

function parseApiErrorBody(data: unknown): ParsedApiError | null {
  if (!data || typeof data !== 'object') return null;
  const body = data as Record<string, unknown>;

  if (typeof body.error === 'string') {
    return {
      error: body.error,
      message: typeof body.message === 'string' ? body.message : '',
      details:
        body.details && typeof body.details === 'object'
          ? (body.details as Record<string, unknown>)
          : undefined,
      field: typeof body.field === 'string' ? body.field : undefined,
    };
  }

  if (body.error && typeof body.error === 'object' && body.error !== null) {
    const nested = body.error as { code?: unknown; message?: unknown };
    if (typeof nested.code === 'string') {
      return {
        error: nested.code,
        message: typeof nested.message === 'string' ? nested.message : '',
        details:
          body.details && typeof body.details === 'object'
            ? (body.details as Record<string, unknown>)
            : undefined,
        field: typeof body.field === 'string' ? body.field : undefined,
      };
    }
  }

  return null;
}

export function mapApiError(error: unknown, context?: ErrorContext): DomainError {
  if (
    typeof error === 'object'
    && error !== null
    && 'code' in error
    && 'message' in error
    && 'severity' in error
  ) {
    return error as DomainError;
  }

  if (error instanceof AxiosError && error.response?.data) {
    const parsed = parseApiErrorBody(error.response.data);
    const fallback = error.response.data as { detail?: unknown };
    const code = parsed?.error ?? 'unknown_error';
    let message = parsed?.message ?? '';

    if (!message && typeof fallback.detail === 'string') {
      message = fallback.detail;
    }

    return {
      code,
      message: message || 'An unexpected error occurred',
      severity: error.response.status >= 500 ? 'error' : 'info',
      title: context?.domain ? `${context.domain} failed` : 'Request failed',
      description: message || undefined,
      details: parsed?.details,
      field: parsed?.field,
      statusCode: error.response.status,
    };
  }

  if (error instanceof AxiosError && !error.response) {
    return {
      code: 'network_error',
      message: 'Network connection failed',
      severity: 'error',
      title: 'network_error',
      description: 'Unable to reach the server.',
    };
  }

  return {
    code: 'unknown_error',
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
    severity: 'error',
    title: 'unknown_error',
  };
}

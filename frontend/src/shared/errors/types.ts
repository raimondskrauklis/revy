// frontend/src/shared/errors/types.ts
export interface DomainError {
  code: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  details?: Record<string, unknown>;
  field?: string;
  statusCode?: number;
}

export interface FieldError {
  field: string;
  message: string;
}

/** Flat API error body — canonical per docs/errors/OBSERVABILITY.md */
export interface FlatApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
  field?: string;
}

export interface ErrorContext {
  domain?: string;
  operation?: string;
}

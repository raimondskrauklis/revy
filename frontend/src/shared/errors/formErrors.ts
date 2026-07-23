// frontend/src/shared/errors/formErrors.ts
import i18n from '@/i18n/config';
import { AxiosError } from 'axios';

function messageForCode(code: string | undefined, fallback: string): string {
  if (!code) return fallback;
  return i18n.t(`errors.${code}`, { defaultValue: fallback });
}

export function handleFormError(
  error: unknown,
  setError: (field: string, error: { type: string; message: string }) => void,
) {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as {
      error?: string | { code?: string; message?: string };
      message?: string;
      field?: string;
    };
    const code =
      typeof data.error === 'string'
        ? data.error
        : data.error && typeof data.error === 'object'
          ? data.error.code
          : undefined;
    const rawMessage =
      typeof data.message === 'string'
        ? data.message
        : data.error && typeof data.error === 'object' && typeof data.error.message === 'string'
          ? data.error.message
          : 'An error occurred';
    const message = messageForCode(code, rawMessage);

    if (data.field) {
      setError(data.field, { type: 'server', message });
      return;
    }
    setError('root', { type: 'server', message });
    return;
  }

  setError('root', {
    type: 'server',
    message:
      error instanceof Error
        ? error.message
        : i18n.t('errors.unknown_error'),
  });
}

// frontend/src/shared/errors/toasts.ts
import i18n from '@/i18n/config';
import { toast as sonnerToast } from 'sonner';
import type { DomainError } from './types';

const recent = new Map<string, number>();
const COOLDOWN_MS = 3000;

function isDuplicate(key: string): boolean {
  const last = recent.get(key);
  const now = Date.now();
  if (last && now - last < COOLDOWN_MS) return true;
  recent.set(key, now);
  setTimeout(() => recent.delete(key), COOLDOWN_MS);
  return false;
}

export const notify = {
  success(title: string, description?: string) {
    const key = `success:${title}`;
    if (isDuplicate(key)) return;
    sonnerToast.success(title, { description });
  },
  error(title: string, description?: string) {
    const key = `error:${title}`;
    if (isDuplicate(key)) return;
    sonnerToast.error(title, { description, duration: Infinity });
  },
  warning(title: string, description?: string) {
    const key = `warning:${title}`;
    if (isDuplicate(key)) return;
    sonnerToast.warning(title, { description, duration: 5000 });
  },
  info(title: string, description?: string) {
    const key = `info:${title}`;
    if (isDuplicate(key)) return;
    sonnerToast.info(title, { description, duration: 3000 });
  },
};

export function showDomainErrorToast(error: DomainError) {
  const key = `domain:${error.code}`;
  if (isDuplicate(key)) return;
  const title = i18n.t(`errors.${error.code}`, {
    defaultValue: error.message,
  });
  const fn = { error: sonnerToast.error, warning: sonnerToast.warning, info: sonnerToast.info }[
    error.severity
  ];
  fn(title, {
    description: error.description,
    duration: error.severity === 'error' ? Infinity : 5000,
  });
}

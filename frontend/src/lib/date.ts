// frontend/src/lib/date.ts
import { format, formatDistanceToNow, isValid, parseISO, startOfDay } from 'date-fns';
import { getDateLocale } from '@/lib/locale';

export function parseApiDate(isoString: string | null | undefined): Date | null {
  if (!isoString) return null;
  try {
    const date = parseISO(isoString);
    return isValid(date) ? date : null;
  } catch {
    return null;
  }
}

export function formatDate(date: Date | string | null | undefined): string {
  const parsed = typeof date === 'string' ? parseApiDate(date) : date;
  if (!parsed || !isValid(parsed)) return '—';
  return format(parsed, 'dd/MM/yyyy', { locale: getDateLocale() });
}

export function formatDateTime(date: Date | string | null | undefined): string {
  const parsed = typeof date === 'string' ? parseApiDate(date) : date;
  if (!parsed || !isValid(parsed)) return '—';
  return format(parsed, 'dd/MM/yyyy, HH:mm', { locale: getDateLocale() });
}

export function formatRelative(date: Date | string | null | undefined): string {
  const parsed = typeof date === 'string' ? parseApiDate(date) : date;
  if (!parsed || !isValid(parsed)) return '—';
  return formatDistanceToNow(parsed, { addSuffix: true, locale: getDateLocale() });
}

export function toApiDateTime(date: Date | null | undefined): string | null {
  if (!date || !isValid(date)) return null;
  return date.toISOString();
}

export function toApiDate(date: Date | null | undefined): string | null {
  if (!date || !isValid(date)) return null;
  return format(date, 'yyyy-MM-dd');
}

export function toApiDateStartOfDay(date: Date | null | undefined): string | null {
  if (!date || !isValid(date)) return null;
  return startOfDay(date).toISOString();
}

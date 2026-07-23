// frontend/src/lib/number.ts
import { getIntlLocale } from '@/lib/locale';

export function formatNumber(
  value: number | null | undefined,
  options?: {
    locale?: string;
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  },
): string {
  if (value == null || !Number.isFinite(value)) return '—';
  const locale = options?.locale ?? getIntlLocale();
  const maxDigits = options?.maximumFractionDigits ?? 2;
  const minDigits = options?.minimumFractionDigits ?? maxDigits;
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: Math.min(minDigits, maxDigits),
    maximumFractionDigits: maxDigits,
  }).format(value);
}

export function formatCurrency(
  value: number | null | undefined,
  options?: {
    locale?: string;
    currency?: string;
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  },
): string {
  if (value == null || !Number.isFinite(value)) return '—';
  const locale = options?.locale ?? getIntlLocale();
  const currency = options?.currency ?? 'EUR';
  const maxDigits = options?.maximumFractionDigits ?? 2;
  const minDigits = options?.minimumFractionDigits ?? maxDigits;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: Math.min(minDigits, maxDigits),
    maximumFractionDigits: maxDigits,
  }).format(value);
}

export function formatCount(
  value: number | null | undefined,
  options?: { locale?: string },
): string {
  if (value == null || !Number.isFinite(value)) return '—';
  const locale = options?.locale ?? getIntlLocale();
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(
  value: number | null | undefined,
  options?: { locale?: string; minimumFractionDigits?: number; maximumFractionDigits?: number },
): string {
  if (value == null || !Number.isFinite(value)) return '—';
  const locale = options?.locale ?? getIntlLocale();
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: options?.minimumFractionDigits ?? 1,
    maximumFractionDigits: options?.maximumFractionDigits ?? 2,
  }).format(value);
}

// frontend/src/lib/locale.ts
import i18n from '@/i18n/config';
import { enGB, lv } from 'date-fns/locale';
import type { Locale } from 'date-fns';

const DATE_LOCALE_MAP: Record<string, Locale> = {
  en: enGB,
  lv,
};

const INTL_LOCALE_MAP: Record<string, string> = {
  en: 'en-GB',
  lv: 'lv-LV',
};

export function normalizeLanguage(language?: string): string {
  if (!language) return 'en';
  return language.toLowerCase().split('-')[0];
}

export function getDateLocale(language?: string): Locale {
  const normalized = normalizeLanguage(language ?? i18n.language);
  return DATE_LOCALE_MAP[normalized] ?? enGB;
}

export function getIntlLocale(language?: string): string {
  const normalized = normalizeLanguage(language ?? i18n.language);
  return INTL_LOCALE_MAP[normalized] ?? 'en-GB';
}

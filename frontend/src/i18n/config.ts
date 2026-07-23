// frontend/src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import lv from './locales/lv.json';

function syncHtmlLang(lng: string) {
  document.documentElement.setAttribute('lang', lng);
}

i18n.on('languageChanged', syncHtmlLang);

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      lv: { translation: lv },
    },
    fallbackLng: 'en',
    supportedLngs: ['en', 'lv'],
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;

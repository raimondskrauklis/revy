// frontend/src/features/settings/pages/ProfileSettingsPage.tsx
import { type FormEvent, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput } from '@/components/ui/quiet-input';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { useAuth } from '@/contexts/AuthContext';
import { patchMe } from '@/lib/me';
import { COMMON_TIMEZONES } from '@/lib/timezones';
import { normalizeLanguage } from '@/lib/locale';
import i18n from '@/i18n/config';
import { mapApiError } from '@/shared/errors';
import { notify, showDomainErrorToast } from '@/shared/errors/toasts';

const LOCALE_OPTIONS = [
  { value: 'en', labelKey: 'settings.profile.locales.en' },
  { value: 'lv', labelKey: 'settings.profile.locales.lv' },
] as const;

export function ProfileSettingsPage() {
  const { t } = useTranslation();
  const { user, refetchUser } = useAuth();
  const [fullName, setFullName] = useState('');
  const [locale, setLocale] = useState('en');
  const [timezone, setTimezone] = useState('UTC');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name ?? '');
    setLocale(user.locale ?? 'en');
    setTimezone(user.timezone ?? 'UTC');
  }, [user]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!user) return;

    setFieldErrors({});
    setSubmitting(true);
    try {
      await patchMe({
        full_name: fullName.trim() === '' ? null : fullName.trim(),
        locale,
        timezone,
      });
      const me = await refetchUser();
      if (me?.locale) {
        await i18n.changeLanguage(normalizeLanguage(me.locale));
      }
      notify.success(t('settings.profile.saveSuccess'));
    } catch (error) {
      const domainError = mapApiError(error);
      if (domainError.field) {
        setFieldErrors({ [domainError.field]: domainError.message });
      } else {
        showDomainErrorToast(domainError);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.profile')}
      </h1>
      <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.profile.emailLabel')}
          </span>
          <QuietInput value={user.email} disabled readOnly />
        </label>
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.profile.nameLabel')}
          </span>
          <QuietInput
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            disabled={submitting}
            aria-invalid={fieldErrors.full_name != null}
          />
          {fieldErrors.full_name ? (
            <span className="text-sm text-[color:var(--app-danger)]">{fieldErrors.full_name}</span>
          ) : null}
        </label>
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.profile.localeLabel')}
          </span>
          <QuietSelect value={locale} onValueChange={setLocale} disabled={submitting}>
            <QuietSelectTrigger fullWidth>
              <QuietSelectValue />
            </QuietSelectTrigger>
            <QuietSelectContent>
              {LOCALE_OPTIONS.map((option) => (
                <QuietSelectItem key={option.value} value={option.value}>
                  {t(option.labelKey)}
                </QuietSelectItem>
              ))}
            </QuietSelectContent>
          </QuietSelect>
          {fieldErrors.locale ? (
            <span className="text-sm text-[color:var(--app-danger)]">{fieldErrors.locale}</span>
          ) : null}
        </label>
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.profile.timezoneLabel')}
          </span>
          <QuietSelect value={timezone} onValueChange={setTimezone} disabled={submitting}>
            <QuietSelectTrigger fullWidth>
              <QuietSelectValue />
            </QuietSelectTrigger>
            <QuietSelectContent>
              {COMMON_TIMEZONES.map((option) => (
                <QuietSelectItem key={option.value} value={option.value}>
                  {t(option.labelKey)}
                </QuietSelectItem>
              ))}
            </QuietSelectContent>
          </QuietSelect>
          {fieldErrors.timezone ? (
            <span className="text-sm text-[color:var(--app-danger)]">{fieldErrors.timezone}</span>
          ) : null}
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
        >
          {t('common.save')}
        </button>
      </form>
    </div>
  );
}

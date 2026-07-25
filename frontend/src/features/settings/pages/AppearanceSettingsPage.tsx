// frontend/src/features/settings/pages/AppearanceSettingsPage.tsx
import { useTranslation } from 'react-i18next';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { useThemeStore } from '@/stores/themeStore';
import type { ThemeMode } from '@/lib/theme';

const THEME_OPTIONS: { value: ThemeMode; labelKey: string }[] = [
  { value: 'light', labelKey: 'theme.light' },
  { value: 'dark', labelKey: 'theme.dark' },
  { value: 'system', labelKey: 'theme.system' },
];

export function AppearanceSettingsPage() {
  const { t } = useTranslation();
  const mode = useThemeStore((state) => state.mode);
  const setMode = useThemeStore((state) => state.setMode);

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.appearance')}
      </h1>
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('settings.appearance.body')}</p>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.appearance.themeLabel')}
        </span>
        <QuietSelect value={mode} onValueChange={(value) => setMode(value as ThemeMode)}>
          <QuietSelectTrigger fullWidth>
            <QuietSelectValue />
          </QuietSelectTrigger>
          <QuietSelectContent>
            {THEME_OPTIONS.map((option) => (
              <QuietSelectItem key={option.value} value={option.value}>
                {t(option.labelKey)}
              </QuietSelectItem>
            ))}
          </QuietSelectContent>
        </QuietSelect>
      </label>
    </div>
  );
}

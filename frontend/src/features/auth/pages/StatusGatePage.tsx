// frontend/src/features/auth/pages/StatusGatePage.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';

interface StatusGatePageProps {
  titleKey: string;
  bodyKey: string;
}

export function StatusGatePage({ titleKey, bodyKey }: StatusGatePageProps) {
  const { t } = useTranslation();
  const { logout } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-[color:var(--app-canvas)] p-6 font-mono">
      <div className="max-w-md space-y-4 rounded-[var(--app-radius-md)] p-6 shadow-[inset_0_0_0_1px_var(--app-ring)]">
        <h1 className="text-xl font-medium text-[color:var(--app-text-strong)]">{t(titleKey)}</h1>
        <p className="font-sans text-sm text-[color:var(--app-text-muted)]">{t(bodyKey)}</p>
        <button
          type="button"
          onClick={() => logout()}
          className="min-h-11 rounded-[var(--app-radius-md)] px-4 shadow-[inset_0_0_0_1px_var(--app-ring)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {t('auth.actions.signOut')}
        </button>
      </div>
    </div>
  );
}

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
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">{t(titleKey)}</h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t(bodyKey)}</p>
        <button
          type="button"
          onClick={() => logout()}
          className="min-h-11 px-4 rounded-lg ring-1 ring-[color:var(--app-ring)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {t('auth.actions.signOut')}
        </button>
      </div>
    </div>
  );
}

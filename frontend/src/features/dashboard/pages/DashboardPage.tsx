// frontend/src/features/dashboard/pages/DashboardPage.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';

export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('nav.dashboard')}
      </h1>
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {t('dashboard.welcome', { email: user?.email ?? '' })}
      </p>
    </div>
  );
}

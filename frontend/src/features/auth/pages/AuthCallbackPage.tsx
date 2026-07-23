// frontend/src/features/auth/pages/AuthCallbackPage.tsx
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function AuthCallbackPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, refetchUser } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
      return;
    }
    void refetchUser().then(() => navigate('/dashboard', { replace: true }));
  }, [isAuthenticated, isLoading, navigate, refetchUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)]">
      <p className="text-[color:var(--app-text-muted)]">{t('auth.loading')}</p>
    </div>
  );
}

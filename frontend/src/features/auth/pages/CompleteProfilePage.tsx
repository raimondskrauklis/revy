// frontend/src/features/auth/pages/CompleteProfilePage.tsx
import { type FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useNavigate } from 'react-router-dom';
import { QuietInput } from '@/components/ui/quiet-input';
import { useAuth } from '@/contexts/AuthContext';
import { completeProfile } from '@/features/auth/api';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function CompleteProfilePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, user, refetchUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!isLoading && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.status === 'active') {
    return <Navigate to="/dashboard" replace />;
  }

  if (user?.status === 'pending_approval') {
    return <Navigate to="/pending-approval" replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFieldError(null);
    const trimmed = fullName.trim();
    if (!trimmed) {
      setFieldError(t('auth.completeProfile.nameRequired'));
      return;
    }

    setSubmitting(true);
    try {
      const updatedUser = await completeProfile({ full_name: trimmed });
      await refetchUser();
      const destination =
        updatedUser.status === 'pending_approval' ? '/pending-approval' : '/dashboard';
      navigate(destination, { replace: true });
    } catch (error) {
      const domainError = mapApiError(error);
      if (domainError.field === 'full_name') {
        setFieldError(domainError.message);
      } else {
        showDomainErrorToast(domainError);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-xl bg-[color:var(--app-surface)] ring-1 ring-[color:var(--app-ring)] p-6 space-y-4"
      >
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('auth.status.completeProfile.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('auth.status.completeProfile.body')}
        </p>
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('auth.completeProfile.nameLabel')}
          </span>
          <QuietInput
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            autoComplete="name"
            disabled={submitting}
            aria-invalid={fieldError != null}
          />
          {fieldError ? (
            <span className="text-sm text-[color:var(--app-danger)]">{fieldError}</span>
          ) : null}
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="min-h-11 w-full rounded-lg bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
        >
          {t('auth.completeProfile.submit')}
        </button>
      </form>
    </div>
  );
}

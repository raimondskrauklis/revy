// frontend/src/features/settings/pages/WorkspaceSettingsPage.tsx
import { type FormEvent, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput } from '@/components/ui/quiet-input';
import { useAuth } from '@/contexts/AuthContext';
import { usePatchWorkspace } from '@/features/settings/hooks';
import { mapApiError } from '@/shared/errors';
import { handleFormError } from '@/shared/errors/formErrors';
import { notify, showDomainErrorToast } from '@/shared/errors/toasts';

export function WorkspaceSettingsPage() {
  const { t } = useTranslation();
  const { user, refetchUser } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const membership = useMemo(
    () => user?.memberships.find((item) => item.workspace_id === workspaceId) ?? null,
    [user?.memberships, workspaceId],
  );

  const [name, setName] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const patchWorkspace = usePatchWorkspace(workspaceId);

  useEffect(() => {
    if (!membership) return;
    setName(membership.workspace_name);
  }, [membership]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!workspaceId) return;

    setFieldErrors({});
    try {
      await patchWorkspace.mutateAsync({ name: name.trim() });
      await refetchUser();
      notify.success(t('settings.workspace.saveSuccess'));
    } catch (error) {
      const domainError = mapApiError(error);
      if (domainError.field) {
        setFieldErrors({ [domainError.field]: domainError.message });
        return;
      }
      handleFormError(error, (field, { message }) => {
        if (field === 'root') {
          showDomainErrorToast(domainError);
        } else {
          setFieldErrors({ [field]: message });
        }
      });
    }
  }

  if (!user || !membership) {
    return null;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.workspace')}
      </h1>
      <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.workspace.nameLabel')}
          </span>
          <QuietInput
            value={name}
            onChange={(event) => setName(event.target.value)}
            disabled={patchWorkspace.isPending}
            aria-invalid={fieldErrors.name != null}
          />
          {fieldErrors.name ? (
            <span className="text-sm text-[color:var(--app-danger)]">{fieldErrors.name}</span>
          ) : null}
        </label>
        <label className="block space-y-1">
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.workspace.slugLabel')}
          </span>
          <QuietInput value={membership.workspace_slug} disabled readOnly />
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.workspace.slugImmutable')}
          </p>
        </label>
        <button
          type="submit"
          disabled={patchWorkspace.isPending}
          className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
        >
          {t('common.save')}
        </button>
      </form>
    </div>
  );
}

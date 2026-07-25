// frontend/src/features/settings/components/InviteMemberForm.tsx
import { type FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput } from '@/components/ui/quiet-input';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { AppRole } from '@/shared/types/enums';
import { mapApiError } from '@/shared/errors';
import { handleFormError } from '@/shared/errors/formErrors';
import { notify, showDomainErrorToast } from '@/shared/errors/toasts';

const ROLE_OPTIONS = [AppRole.admin, AppRole.operator, AppRole.viewer] as const;

interface InviteMemberFormProps {
  onInvite: (payload: { email: string; role: AppRole }) => Promise<void>;
  submitting?: boolean;
}

export function InviteMemberForm({ onInvite, submitting = false }: InviteMemberFormProps) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<AppRole>(AppRole.viewer);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFieldErrors({});

    try {
      await onInvite({ email: email.trim(), role });
      setEmail('');
      setRole(AppRole.viewer);
      notify.success(t('settings.team.invite.success'));
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

  return (
    <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
      <h3 className="text-base font-medium text-[color:var(--app-text-strong)]">
        {t('settings.team.invite.title')}
      </h3>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.team.invite.emailLabel')}
        </span>
        <QuietInput
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={submitting}
          aria-invalid={fieldErrors.email != null}
          required
        />
        {fieldErrors.email ? (
          <span className="text-sm text-[color:var(--app-danger)]">{fieldErrors.email}</span>
        ) : null}
      </label>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.team.invite.roleLabel')}
        </span>
        <QuietSelect value={role} onValueChange={(value) => setRole(value as AppRole)} disabled={submitting}>
          <QuietSelectTrigger fullWidth>
            <QuietSelectValue />
          </QuietSelectTrigger>
          <QuietSelectContent>
            {ROLE_OPTIONS.map((option) => (
              <QuietSelectItem key={option} value={option}>
                {t(`settings.team.roles.${option}`)}
              </QuietSelectItem>
            ))}
          </QuietSelectContent>
        </QuietSelect>
        {fieldErrors.role ? (
          <span className="text-sm text-[color:var(--app-danger)]">{fieldErrors.role}</span>
        ) : null}
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
      >
        {t('settings.team.invite.submit')}
      </button>
    </form>
  );
}

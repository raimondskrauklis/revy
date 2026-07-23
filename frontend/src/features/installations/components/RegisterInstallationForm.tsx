// frontend/src/features/installations/components/RegisterInstallationForm.tsx
import { type FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput } from '@/components/ui/quiet-input';
import { QuietSelect, QuietSelectContent, QuietSelectItem, QuietSelectTrigger, QuietSelectValue } from '@/components/ui/quiet-select';
import type { RegisterInstallationPayload } from '@/features/installations/api';
import { GitHubAccountType } from '@/shared/types/enums';

interface RegisterInstallationFormProps {
  onSubmit: (payload: RegisterInstallationPayload) => Promise<void>;
  submitting: boolean;
}

export function RegisterInstallationForm({ onSubmit, submitting }: RegisterInstallationFormProps) {
  const { t } = useTranslation();
  const [githubInstallationId, setGithubInstallationId] = useState('');
  const [accountLogin, setAccountLogin] = useState('');
  const [accountId, setAccountId] = useState('');
  const [accountType, setAccountType] = useState<GitHubAccountType>(GitHubAccountType.organization);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await onSubmit({
      github_installation_id: Number(githubInstallationId),
      account_login: accountLogin.trim(),
      account_type: accountType,
      account_id: Number(accountId),
    });
    setGithubInstallationId('');
    setAccountLogin('');
    setAccountId('');
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-xl bg-[color:var(--app-surface)] ring-1 ring-[color:var(--app-ring)] p-4"
    >
      <h2 className="text-base font-semibold text-[color:var(--app-text-strong)]">
        {t('installations.register.title')}
      </h2>
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {t('installations.register.description')}
      </p>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('installations.register.installationId')}
        </span>
        <QuietInput
          value={githubInstallationId}
          onChange={(event) => setGithubInstallationId(event.target.value)}
          inputMode="numeric"
          disabled={submitting}
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('installations.register.accountLogin')}
        </span>
        <QuietInput
          value={accountLogin}
          onChange={(event) => setAccountLogin(event.target.value)}
          disabled={submitting}
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('installations.register.accountId')}
        </span>
        <QuietInput
          value={accountId}
          onChange={(event) => setAccountId(event.target.value)}
          inputMode="numeric"
          disabled={submitting}
          required
        />
      </label>
      <label className="block space-y-1">
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('installations.register.accountType')}
        </span>
        <QuietSelect
          value={accountType}
          onValueChange={(value) => setAccountType(value as GitHubAccountType)}
          disabled={submitting}
        >
          <QuietSelectTrigger fullWidth>
            <QuietSelectValue placeholder={t('common.select')} />
          </QuietSelectTrigger>
          <QuietSelectContent>
            <QuietSelectItem value={GitHubAccountType.organization}>
              {t('installations.accountType.organization')}
            </QuietSelectItem>
            <QuietSelectItem value={GitHubAccountType.user}>
              {t('installations.accountType.user')}
            </QuietSelectItem>
          </QuietSelectContent>
        </QuietSelect>
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
      >
        {t('installations.register.submit')}
      </button>
    </form>
  );
}

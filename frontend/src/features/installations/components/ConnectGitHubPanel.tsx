// frontend/src/features/installations/components/ConnectGitHubPanel.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RegisterInstallationForm } from '@/features/installations/components/RegisterInstallationForm';
import type { RegisterInstallationPayload } from '@/features/installations/api';

const CARD_KEYS = ['orgOwner', 'sso', 'selectRepos', 'authorizeVsInstall'] as const;

interface ConnectGitHubPanelProps {
  connecting: boolean;
  submittingFallback: boolean;
  onConnect: () => Promise<void>;
  onFallbackSubmit: (payload: RegisterInstallationPayload) => Promise<void>;
}

export function ConnectGitHubPanel({
  connecting,
  submittingFallback,
  onConnect,
  onFallbackSubmit,
}: ConnectGitHubPanelProps) {
  const { t } = useTranslation();
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const busy = connecting || submittingFallback;

  return (
    <section className="space-y-4">
      <div className="space-y-3 rounded-xl bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
        <h2 className="text-base font-semibold text-[color:var(--app-text-strong)]">
          {t('installations.connect.title')}
        </h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          {CARD_KEYS.map((key) => (
            <li
              key={key}
              className="rounded-lg bg-[color:var(--app-chip)] p-3"
            >
              <p className="text-sm font-medium text-[color:var(--app-text-strong)]">
                {t(`installations.connect.cards.${key}.title`)}
              </p>
              <p className="mt-1 text-sm text-[color:var(--app-text-muted)]">
                {t(`installations.connect.cards.${key}.body`)}
              </p>
            </li>
          ))}
        </ul>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            void onConnect();
          }}
          className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
        >
          {connecting
            ? t('installations.connect.installing')
            : t('installations.connect.install')}
        </button>
      </div>

      <details
        className="rounded-xl bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]"
        onToggle={(event) => {
          setFallbackOpen(event.currentTarget.open);
        }}
      >
        <summary className="min-h-11 cursor-pointer text-sm text-[color:var(--app-text-muted)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]">
          {t('installations.register.fallbackSummary')}
        </summary>
        {fallbackOpen ? (
          <div className="mt-4">
            <RegisterInstallationForm
              embedded
              onSubmit={onFallbackSubmit}
              submitting={submittingFallback}
            />
          </div>
        ) : null}
      </details>
    </section>
  );
}

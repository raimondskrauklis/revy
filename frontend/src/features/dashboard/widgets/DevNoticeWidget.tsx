// frontend/src/features/dashboard/widgets/DevNoticeWidget.tsx
import { useTranslation } from 'react-i18next';

export function DevNoticeWidget() {
  const { t } = useTranslation();

  return (
    <section className="space-y-3 rounded-lg border border-[color:var(--app-primary)] bg-[color:var(--app-surface)] p-4">
      <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
        {t('dashboard.devNotice.title')}
      </h2>
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {t('dashboard.devNotice.body')}
      </p>
      <a
        href="https://github.com/raimondskrauklis/revy/issues/new"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex min-h-11 items-center justify-center rounded-[var(--app-radius-md)] bg-[color:var(--app-primary)] px-4 text-sm font-medium text-[color:var(--app-on-accent)] hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {t('dashboard.devNotice.feedback')}
      </a>
    </section>
  );
}
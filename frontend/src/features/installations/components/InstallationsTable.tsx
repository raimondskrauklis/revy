// frontend/src/features/installations/components/InstallationsTable.tsx
import { useTranslation } from 'react-i18next';
import { QuietChipStatus } from '@/components/ui/quiet-chip';
import { formatDateTime } from '@/lib/date';
import type { GitHubInstallation } from '@/features/installations/api';

interface InstallationsTableProps {
  installations: GitHubInstallation[];
}

export function InstallationsTable({ installations }: InstallationsTableProps) {
  const { t } = useTranslation();

  if (installations.length === 0) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {t('installations.empty')}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto ring-1 ring-[color:var(--app-ring)] rounded-lg">
      <table className="min-w-full text-sm">
        <thead className="bg-[color:var(--app-table-header)] text-[color:var(--app-text-muted)]">
          <tr>
            <th className="px-4 py-3 text-left font-medium">{t('installations.table.account')}</th>
            <th className="px-4 py-3 text-left font-medium">{t('installations.table.type')}</th>
            <th className="px-4 py-3 text-left font-medium">{t('installations.table.installationId')}</th>
            <th className="px-4 py-3 text-left font-medium">{t('installations.table.status')}</th>
            <th className="px-4 py-3 text-left font-medium">{t('installations.table.verified')}</th>
            <th className="px-4 py-3 text-left font-medium">{t('installations.table.created')}</th>
          </tr>
        </thead>
        <tbody>
          {installations.map((installation, index) => (
            <tr
              key={installation.id}
              className={
                index % 2 === 0
                  ? 'bg-[color:var(--app-table-row)]'
                  : 'bg-[color:var(--app-table-row-alt)]'
              }
            >
              <td className="px-4 py-3 text-[color:var(--app-text-strong)]">
                {installation.account_login}
              </td>
              <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                {t(`installations.accountType.${installation.account_type}`)}
              </td>
              <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                {installation.github_installation_id}
              </td>
              <td className="px-4 py-3">
                <QuietChipStatus
                  intent={installation.status === 'active' ? 'success' : 'default'}
                  variant="quiet"
                  placement="dataRow"
                >
                  {t(`installations.status.${installation.status}`)}
                </QuietChipStatus>
              </td>
              <td className="px-4 py-3">
                {installation.verified_at ? (
                  <span className="text-[color:var(--app-text-muted)]">
                    {t('installations.verified.yes')}
                  </span>
                ) : (
                  <a
                    href={`https://github.com/settings/installations/${installation.github_installation_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-[color:var(--app-link)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
                  >
                    {t('installations.verified.configure')}
                  </a>
                )}
              </td>
              <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                {formatDateTime(installation.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

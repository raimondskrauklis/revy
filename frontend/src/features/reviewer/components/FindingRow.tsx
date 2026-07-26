// frontend/src/features/reviewer/components/FindingRow.tsx
import { useTranslation } from 'react-i18next';
import type { ReconciledFinding } from '@/features/reviewer/types';

interface FindingRowProps {
  finding: ReconciledFinding;
}

export function FindingRow({ finding }: FindingRowProps) {
  const { t } = useTranslation();

  return (
    <tr className="border-t border-[color:var(--app-ring)]">
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-strong)]">
        {t(`reviewer.severity.${finding.severity}`)}
      </td>
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-muted)]">
        {t(`reviewer.category.${finding.category}`)}
      </td>
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-muted)]">
        {t(`reviewer.groupState.${finding.state}`)}
      </td>
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-strong)]">{finding.title}</td>
      <td className="px-3 py-2 text-sm font-mono text-[color:var(--app-text-muted)]">
        {finding.file_path ?? '—'}
      </td>
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-muted)]">{finding.message}</td>
    </tr>
  );
}

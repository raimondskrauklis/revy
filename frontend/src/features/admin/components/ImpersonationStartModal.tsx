// frontend/src/features/admin/components/ImpersonationStartModal.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput } from '@/components/ui/quiet-input';
import { Button } from '@/components/ui/button';

interface ImpersonationStartModalProps {
  targetEmail: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: (reason: string) => void;
}

export function ImpersonationStartModal({
  targetEmail,
  busy,
  onCancel,
  onConfirm,
}: ImpersonationStartModalProps) {
  const { t } = useTranslation();
  const [reason, setReason] = useState('');

  const trimmed = reason.trim();
  const canSubmit = trimmed.length >= 10;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="impersonation-modal-title"
      className="rounded-lg bg-[color:var(--app-chip)] p-4 space-y-4"
    >
      <div>
        <h2
          id="impersonation-modal-title"
          className="text-sm font-semibold text-[color:var(--app-text-strong)]"
        >
          {t('admin.impersonation.startTitle')}
        </h2>
        <p className="mt-1 text-sm text-[color:var(--app-text-muted)]">
          {t('admin.impersonation.startDescription', { email: targetEmail })}
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="impersonation-reason" className="text-xs font-medium text-[color:var(--app-text-muted)]">
          {t('admin.impersonation.reasonLabel')}
        </label>
        <QuietInput
          id="impersonation-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder={t('admin.impersonation.reasonPlaceholder')}
          aria-label={t('admin.impersonation.reasonLabel')}
        />
        <p className="text-xs text-[color:var(--app-text-muted)]">{t('admin.impersonation.reasonHint')}</p>
      </div>

      <div className="flex gap-2">
        <Button
          type="button"
          disabled={busy || !canSubmit}
          onClick={() => onConfirm(trimmed)}
        >
          {busy ? t('common.loading') : t('admin.impersonation.start')}
        </Button>
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          {t('common.cancel')}
        </Button>
      </div>
    </div>
  );
}

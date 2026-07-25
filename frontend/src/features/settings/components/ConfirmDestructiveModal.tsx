// frontend/src/features/settings/components/ConfirmDestructiveModal.tsx
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput } from '@/components/ui/quiet-input';

interface ConfirmDestructiveModalProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  confirmMatch?: string;
  confirmMatchLabel?: string;
  isLoading?: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function ConfirmDestructiveModal({
  open,
  title,
  description,
  confirmLabel,
  confirmMatch,
  confirmMatchLabel,
  isLoading = false,
  onClose,
  onConfirm,
}: ConfirmDestructiveModalProps) {
  const { t } = useTranslation();
  const [typedValue, setTypedValue] = useState('');

  useEffect(() => {
    if (!open) {
      setTypedValue('');
    }
  }, [open]);

  if (!open) {
    return null;
  }

  const requiresMatch = Boolean(confirmMatch);
  const canConfirm = !requiresMatch || typedValue === confirmMatch;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[color-mix(in_oklab,var(--app-text-strong)_45%,transparent)] p-4"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="destructive-modal-title"
        className="w-full max-w-md space-y-4 rounded-lg bg-[color:var(--app-surface)] p-5 ring-1 ring-[color:var(--app-ring)]"
        onClick={(event) => event.stopPropagation()}
      >
        <h2
          id="destructive-modal-title"
          className="text-lg font-semibold text-[color:var(--app-danger)]"
        >
          {title}
        </h2>
        <p className="text-sm text-[color:var(--app-text-muted)]">{description}</p>

        {requiresMatch ? (
          <div className="space-y-2">
            <label
              htmlFor="destructive-confirm-input"
              className="block text-sm text-[color:var(--app-text-strong)]"
            >
              {confirmMatchLabel}
            </label>
            <QuietInput
              id="destructive-confirm-input"
              value={typedValue}
              onChange={(event) => setTypedValue(event.target.value)}
              autoComplete="off"
            />
          </div>
        ) : null}

        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="min-h-11 rounded-lg px-4 text-sm text-[color:var(--app-text-strong)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
          >
            {t('common.cancel')}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading || !canConfirm}
            className="min-h-11 rounded-lg bg-[color:var(--app-danger)] px-4 text-sm font-medium text-[color:var(--app-on-accent)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// frontend/src/components/ui/quiet-chip.tsx

import * as React from 'react';
import { X, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

type Intent = 'default' | 'info' | 'success' | 'warn' | 'danger';

export type QuietChipStatusIntent = Intent;
export type QuietChipStatusPlacement = 'panel' | 'dataRow';

const intentClasses: Record<Intent, string> = {
  default:
    'shadow-[inset_0_0_0_1px_var(--app-input-border)] bg-[color:var(--app-surface)] text-[color:var(--app-text)]',
  info:
    'bg-[color-mix(in_oklab,var(--app-info)_12%,transparent)] text-[color:var(--app-info)] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--app-info)_30%,transparent)]',
  success:
    'bg-[color-mix(in_oklab,var(--app-success)_12%,transparent)] text-[color:var(--app-success)] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--app-success)_30%,transparent)]',
  warn:
    'bg-[color-mix(in_oklab,var(--app-warning)_12%,transparent)] text-[color:var(--app-warning)] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--app-warning)_30%,transparent)]',
  danger:
    'bg-[color-mix(in_oklab,var(--app-danger)_12%,transparent)] text-[color:var(--app-danger)] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--app-danger)_30%,transparent)]',
};

const quietDefaultDataRow =
  'shadow-[inset_0_0_0_1px_var(--app-input-border)] bg-[color:var(--app-chip-active)] text-[color:var(--app-text)]';

type BaseProps = {
  size?: 'sm' | 'md';
  className?: string;
  children?: React.ReactNode;
};

export function QuietChipLabel({
  size = 'sm',
  placement = 'panel',
  className,
  children,
  ...rest
}: BaseProps & {
  placement?: QuietChipStatusPlacement;
} & React.HTMLAttributes<HTMLSpanElement>) {
  const fillClass = placement === 'dataRow' ? quietDefaultDataRow : intentClasses.default;
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full leading-snug',
        size === 'sm' ? 'min-h-7 px-2.5 py-1 text-[12px]' : 'min-h-8 px-3 py-1.5 text-sm',
        fillClass,
        'hover:bg-[color:var(--app-chip)]',
        className
      )}
      {...rest}
    >
      {children}
    </span>
  );
}

export function QuietChipSelectable({
  selected,
  onToggle,
  size = 'sm',
  className,
  children,
  disabled,
}: BaseProps & {
  selected?: boolean;
  onToggle?: (next: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={!!selected}
      disabled={disabled}
      onClick={() => onToggle?.(!selected)}
      className={cn(
        'inline-flex items-center gap-1 rounded-full transition',
        size === 'sm' ? 'min-h-7 px-2.5 py-1 text-[12px] leading-snug' : 'min-h-8 px-3 py-1.5 text-sm leading-snug',
        'outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)] focus-visible:ring-offset-1 focus-visible:ring-offset-[color:var(--app-surface)]',
        selected
          ? 'bg-[color:var(--app-chip-active)] shadow-[inset_0_0_0_1px_var(--app-ring)]'
          : cn(intentClasses.default, 'hover:bg-[color:var(--app-chip)]'),
        disabled && 'opacity-50 pointer-events-none',
        className
      )}
    >
      {selected && <Check className="size-3.5 opacity-70" />}
      <span className="truncate">{children}</span>
    </button>
  );
}

export function QuietChipStatus({
  intent = 'default',
  size = 'sm',
  variant = 'quiet',
  placement = 'panel',
  className,
  children,
}: BaseProps & {
  intent?: Intent;
  variant?: 'quiet' | 'minimal';
  placement?: QuietChipStatusPlacement;
}) {
  const quietClass =
    variant === 'quiet'
      ? placement === 'dataRow' && intent === 'default'
        ? quietDefaultDataRow
        : intentClasses[intent]
      : null;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full leading-snug',
        size === 'sm' ? 'min-h-6 px-2.5 py-1 text-xs' : 'min-h-7 px-3 py-1 text-[13px]',
        variant === 'minimal'
          ? intent === 'info'
            ? 'bg-transparent text-[color:var(--app-info)]'
            : intent === 'success'
              ? 'bg-transparent text-[color:var(--app-success)]'
              : intent === 'warn'
                ? 'bg-transparent text-[color:var(--app-warning)]'
                : intent === 'danger'
                  ? 'bg-transparent text-[color:var(--app-danger)]'
                  : 'bg-transparent text-[color:var(--app-text)]'
          : quietClass,
        className
      )}
    >
      {children}
    </span>
  );
}

export function QuietChipTag({
  onDismiss,
  size = 'sm',
  placement = 'panel',
  className,
  children,
}: BaseProps & {
  onDismiss?: () => void;
  placement?: QuietChipStatusPlacement;
}) {
  const { t } = useTranslation();
  const fillClass = placement === 'dataRow' ? quietDefaultDataRow : intentClasses.default;
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full leading-snug',
        size === 'sm' ? 'min-h-7 pl-2 pr-1.5 py-1 text-[12px]' : 'min-h-8 pl-2.5 pr-2 py-1.5 text-sm',
        fillClass,
        'hover:bg-[color:var(--app-chip)]',
        className
      )}
    >
      <span className="truncate">{children}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="ml-1.5 grid place-items-center rounded-full p-0.5 outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]"
          aria-label={t('common.remove')}
        >
          <X className="size-3.5 opacity-70" />
        </button>
      )}
    </span>
  );
}

// frontend/src/components/ui/quiet-date.tsx

import { useMemo, useState, useCallback } from 'react';
import { CalendarIcon, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { startOfDay } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { formatDate } from '@/lib/date';
import { cn } from '@/lib/utils';

const DEFAULT_START_MONTH = new Date(2016, 0, 1);
const getDefaultEndMonth = () => new Date(new Date().getFullYear(), 11, 31);

type QuietDateInputProps = {
  value?: Date;
  onChange?: (value: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  minDate?: Date;
  maxDate?: Date;
  className?: string;
};

export function QuietDateInput({
  value,
  onChange,
  placeholder,
  disabled,
  minDate,
  maxDate,
  className,
}: QuietDateInputProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const displayValue = useMemo(() => {
    if (!value) return placeholder ?? t('common.selectDate');
    return formatDate(value);
  }, [value, placeholder, t]);

  const handleClear = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onChange?.(undefined);
    },
    [onChange]
  );

  const handleToday = useCallback(() => {
    const today = startOfDay(new Date());
    const minDay = minDate ? startOfDay(minDate) : null;
    const maxDay = maxDate ? startOfDay(maxDate) : null;

    if (minDay && today < minDay) return;
    if (maxDay && today > maxDay) return;
    onChange?.(today);
    setOpen(false);
  }, [onChange, minDate, maxDate]);

  const isTodayDisabled = (() => {
    const today = startOfDay(new Date());
    const minDay = minDate ? startOfDay(minDate) : null;
    const maxDay = maxDate ? startOfDay(maxDate) : null;

    if (minDay && today < minDay) return true;
    if (maxDay && today > maxDay) return true;
    return false;
  })();

  const startMonth = minDate ?? DEFAULT_START_MONTH;
  const endMonth = maxDate ?? getDefaultEndMonth();

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          disabled={disabled}
          className={cn(
            'w-full justify-between gap-2',
            'bg-[color:var(--app-surface)] text-[color:var(--app-text)]',
            'shadow-[inset_0_0_0_1px_var(--app-input-border)] rounded-lg px-3 h-11',
            'hover:bg-[color:var(--app-chip)]',
            'focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]',
            'focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--app-surface)]',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            className
          )}
        >
          <span
            className={cn(
              'truncate',
              value ? 'text-[color:var(--app-text-strong)]' : 'text-[color:var(--app-text-muted)]'
            )}
          >
            {displayValue}
          </span>
          <div className="flex items-center gap-1 shrink-0">
            {value && !disabled && (
              <span
                role="button"
                tabIndex={0}
                aria-label={t('common.clear')}
                className="p-0.5 rounded hover:bg-[color:var(--app-ring)] transition-colors"
                onClick={handleClear}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleClear(e as unknown as React.MouseEvent);
                  }
                }}
              >
                <X className="h-3.5 w-3.5 text-[color:var(--app-text-muted)]" />
              </span>
            )}
            <CalendarIcon className="h-4 w-4 text-[color:var(--app-text-muted)]" />
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" sideOffset={4} className="w-auto p-0 min-w-[320px]">
        <Calendar
          mode="single"
          selected={value}
          onSelect={(day) => {
            onChange?.(day ?? undefined);
            setOpen(false);
          }}
          weekStartsOn={1}
          captionLayout="label"
          startMonth={startMonth}
          endMonth={endMonth}
          disabled={(date) => {
            const day = startOfDay(date);
            const minDay = minDate ? startOfDay(minDate) : null;
            const maxDay = maxDate ? startOfDay(maxDate) : null;
            if (minDay && day < minDay) return true;
            if (maxDay && day > maxDay) return true;
            return false;
          }}
          defaultMonth={value ?? minDate ?? new Date()}
        />
        <div className="flex items-center justify-end gap-2 px-3 py-2.5 shadow-[inset_0_1px_0_0_var(--app-ring)] bg-[color:var(--app-surface)]">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-3 text-[color:var(--app-text-muted)] hover:text-[color:var(--app-text)]"
            onClick={() => {
              onChange?.(undefined);
              setOpen(false);
            }}
          >
            {t('common.clear')}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={isTodayDisabled}
            className="h-8 px-3 font-medium text-[color:var(--app-link)] hover:bg-[color:var(--app-chip)]"
            onClick={handleToday}
          >
            {t('common.today')}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

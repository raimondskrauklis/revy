// frontend/src/components/ui/calendar.tsx

import * as React from 'react';
import { DayPicker } from 'react-day-picker';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getDateLocale } from '@/lib/locale';

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

function CalendarChevron({ orientation }: { orientation?: 'left' | 'right' | 'up' | 'down' }) {
  const iconClass = 'h-4 w-4';
  if (orientation === 'left') return <ChevronLeft className={iconClass} />;
  return <ChevronRight className={iconClass} />;
}

export function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  weekStartsOn = 1,
  locale = getDateLocale(),
  captionLayout = 'label',
  ...props
}: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      weekStartsOn={weekStartsOn as 0 | 1 | 2 | 3 | 4 | 5 | 6}
      locale={locale}
      captionLayout={captionLayout}
      className={cn('p-3 min-w-[280px]', className)}
      components={{ Chevron: CalendarChevron }}
      classNames={{
        months: 'flex flex-col sm:flex-row gap-4',
        month: 'space-y-4',
        month_caption: 'flex justify-center pt-1 relative items-center gap-2',
        caption_label: 'text-sm font-medium text-[color:var(--app-text-strong)]',
        nav: 'flex items-center gap-1',
        button_previous: cn(
          'absolute left-0 top-1/2 -translate-y-1/2 h-8 w-8 min-w-[2rem] bg-transparent p-0 inline-flex items-center justify-center rounded-md',
          'text-[color:var(--app-text-muted)] hover:text-[color:var(--app-text)] hover:bg-[color:var(--app-chip)]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]',
          'disabled:opacity-50 disabled:pointer-events-none'
        ),
        button_next: cn(
          'absolute right-0 top-1/2 -translate-y-1/2 h-8 w-8 min-w-[2rem] bg-transparent p-0 inline-flex items-center justify-center rounded-md',
          'text-[color:var(--app-text-muted)] hover:text-[color:var(--app-text)] hover:bg-[color:var(--app-chip)]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]',
          'disabled:opacity-50 disabled:pointer-events-none'
        ),
        month_grid: 'w-full border-collapse',
        weekdays: 'grid grid-cols-7',
        weekday: 'text-[color:var(--app-text-muted)] rounded-md w-9 font-normal text-[0.8rem] text-center',
        week: 'grid grid-cols-7 mt-2',
        day: cn(
          'h-9 w-9 text-center text-sm p-0 relative',
          '[&:has([aria-selected])]:bg-[color:var(--app-chip)]',
          'focus-within:relative focus-within:z-20'
        ),
        day_button: cn(
          'h-9 w-9 p-0 font-normal inline-flex items-center justify-center rounded-md',
          'text-[color:var(--app-text)] transition-colors',
          'hover:bg-[color:var(--app-chip)] hover:text-[color:var(--app-text-strong)]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]',
          'aria-selected:opacity-100'
        ),
        selected: cn(
          'bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)]',
          'hover:bg-[color:var(--app-cta-bg)] hover:text-[color:var(--app-cta-fg)]',
          'focus:bg-[color:var(--app-cta-bg)] focus:text-[color:var(--app-cta-fg)]'
        ),
        today: 'bg-[color:var(--app-chip)] text-[color:var(--app-text-strong)] font-semibold',
        outside: 'text-[color:var(--app-text-muted)] opacity-50',
        disabled: 'text-[color:var(--app-text-muted)] opacity-50 cursor-not-allowed',
        hidden: 'invisible',
        ...classNames,
      }}
      {...props}
    />
  );
}

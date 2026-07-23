// frontend/src/components/ui/quiet-input.tsx

import * as React from 'react';
import { cn } from '@/lib/utils';

const BaseInput = React.forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(function BaseInput(
  { className, type, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      type={type}
      data-slot="input"
      className={cn(
        'h-9 w-full min-w-0 rounded-md bg-transparent px-3 py-1 text-base md:text-sm',
        'placeholder:text-[color:var(--app-text-muted)] transition-[color,box-shadow] outline-none disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  );
});

const BaseTextarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<'textarea'>>(function BaseTextarea(
  { className, ...props },
  ref
) {
  return (
    <textarea
      ref={ref}
      data-slot="textarea"
      className={cn(
        'flex min-h-[80px] w-full rounded-md bg-transparent px-3 py-2 text-base md:text-sm',
        'placeholder:text-[color:var(--app-text-muted)] transition-[color,box-shadow] outline-none disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  );
});

export const QuietInput = React.forwardRef<HTMLInputElement, React.ComponentProps<typeof BaseInput>>(function QuietInput(
  { className, ...props },
  ref
) {
  return (
    <BaseInput
      ref={ref}
      className={cn(
        'h-11 rounded-lg border-0 shadow-none',
        'bg-[color:var(--app-surface)] text-[color:var(--app-text)]',
        'shadow-[inset_0_0_0_1px_var(--app-input-border)] hover:bg-[color:var(--app-chip)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)] focus-visible:ring-offset-1 focus-visible:ring-offset-[color:var(--app-surface)]',
        className
      )}
      {...props}
    />
  );
});

export const QuietTextarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<typeof BaseTextarea>>(function QuietTextarea(
  { className, ...props },
  ref
) {
  return (
    <BaseTextarea
      ref={ref}
      className={cn(
        'rounded-lg border-0 shadow-none',
        'bg-[color:var(--app-surface)] text-[color:var(--app-text)]',
        'shadow-[inset_0_0_0_1px_var(--app-input-border)] hover:bg-[color:var(--app-chip)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)] focus-visible:ring-offset-1 focus-visible:ring-offset-[color:var(--app-surface)]',
        className
      )}
      {...props}
    />
  );
});

export default QuietInput;

// frontend/src/components/ui/skeleton.tsx

import type { ComponentProps } from 'react';
import { cn } from '@/lib/utils';

function Skeleton({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="skeleton"
      className={cn(
        'animate-pulse rounded-md bg-[color:var(--app-chip)]',
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };

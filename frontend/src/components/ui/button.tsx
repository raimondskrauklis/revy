// frontend/src/components/ui/button.tsx

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]",
  {
    variants: {
      variant: {
        default:
          'bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] hover:opacity-90',
        destructive:
          'bg-[color:var(--app-danger)] text-[color:var(--app-on-accent)] hover:opacity-90',
        outline:
          'border-0 bg-transparent text-[color:var(--app-text)] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--app-input-border)_70%,transparent)] hover:bg-[color:var(--app-chip)]',
        secondary:
          'bg-[color:var(--app-chip)] text-[color:var(--app-text)] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--app-input-border)_60%,transparent)] hover:bg-[color:var(--app-chip-active)]',
        ghost:
          'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)] hover:text-[color:var(--app-text)]',
        link: 'text-[color:var(--app-link)] underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2 has-[>svg]:px-3',
        sm: 'h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5',
        lg: 'h-10 rounded-md px-6 has-[>svg]:px-4',
        icon: 'size-9',
        'icon-sm': 'size-8',
        'icon-lg': 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };

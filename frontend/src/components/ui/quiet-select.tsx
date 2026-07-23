// frontend/src/components/ui/quiet-select.tsx

import * as React from 'react';
import * as SelectPrimitive from '@radix-ui/react-select';
import { CheckIcon, ChevronDownIcon, ChevronUpIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export function QuietSelect(props: React.ComponentProps<typeof SelectPrimitive.Root>) {
  return <SelectPrimitive.Root data-slot="quiet-select" {...props} />;
}

export function QuietSelectValue(props: React.ComponentProps<typeof SelectPrimitive.Value>) {
  return <SelectPrimitive.Value data-slot="quiet-select-value" {...props} />;
}

export function QuietSelectTrigger({
  className,
  size = 'md',
  fullWidth = false,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Trigger> & {
  size?: 'sm' | 'md';
  fullWidth?: boolean;
}) {
  return (
    <SelectPrimitive.Trigger
      data-slot="quiet-select-trigger"
      data-size={size}
      className={cn(
        'rounded-lg px-3 outline-none shadow-none flex items-center justify-between gap-2',
        'bg-[color:var(--app-surface)] shadow-[inset_0_0_0_1px_var(--app-input-border)]',
        'text-[color:var(--app-text)] [&_svg]:text-[color:var(--app-text-muted)]',
        'hover:bg-[color:var(--app-chip)] data-[state=open]:bg-[color:var(--app-chip-active)]',
        'focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)] focus-visible:ring-offset-1 focus-visible:ring-offset-[color:var(--app-surface)]',
        'data-[state=open]:ring-2 data-[state=open]:ring-[color:var(--app-ring-strong)] data-[state=open]:ring-offset-1 data-[state=open]:ring-offset-[color:var(--app-surface)]',
        size === 'sm' ? 'h-8 text-sm' : 'h-11 text-sm',
        fullWidth ? 'w-full' : 'w-fit',
        className
      )}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon asChild>
        <ChevronDownIcon className="size-4 opacity-60" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
}

export function QuietSelectContent({
  className,
  children,
  position = 'popper',
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Content>) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        data-slot="quiet-select-content"
        className={cn(
          'bg-[color:var(--app-surface)] text-[color:var(--app-text)] shadow-[var(--elev-shadow-2)] rounded-md z-[var(--z-dropdown)] overflow-hidden',
          'flex flex-col max-h-[var(--radix-select-content-available-height,15rem)]',
          position === 'popper' && 'data-[side=bottom]:translate-y-1',
          className
        )}
        position={position}
        {...props}
      >
        <QuietSelectScrollUpButton />
        <SelectPrimitive.Viewport className={cn('p-1 app-scroll flex-1 min-h-0 overflow-y-auto')}>
          {children}
        </SelectPrimitive.Viewport>
        <QuietSelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

export function QuietSelectItem({
  className,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Item>) {
  return (
    <SelectPrimitive.Item
      data-slot="quiet-select-item"
      className={cn(
        'relative flex w-full cursor-default select-none items-center gap-2 rounded-md py-1.5 pr-8 pl-2 text-sm',
        'text-[color:var(--app-text)] outline-none',
        'hover:bg-[color:var(--app-chip)] focus:bg-[color:var(--app-chip)] data-[highlighted]:bg-[color:var(--app-chip)] data-[state=checked]:bg-[color:var(--app-chip-active)]',
        className
      )}
      {...props}
    >
      <span className="absolute right-2 flex size-3.5 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}

export function QuietSelectLabel({ className, ...props }: React.ComponentProps<typeof SelectPrimitive.Label>) {
  return (
    <SelectPrimitive.Label
      className={cn('px-2 py-1.5 text-xs text-[color:var(--app-text-muted)]', className)}
      {...props}
    />
  );
}

export function QuietSelectSeparator({ className, ...props }: React.ComponentProps<typeof SelectPrimitive.Separator>) {
  return <SelectPrimitive.Separator className={cn('bg-[color:var(--app-ring)] -mx-1 my-1 h-px', className)} {...props} />;
}

export function QuietSelectScrollUpButton({ className, ...props }: React.ComponentProps<typeof SelectPrimitive.ScrollUpButton>) {
  return (
    <SelectPrimitive.ScrollUpButton className={cn('flex items-center justify-center py-1', className)} {...props}>
      <ChevronUpIcon className="size-4" />
    </SelectPrimitive.ScrollUpButton>
  );
}

export function QuietSelectScrollDownButton({ className, ...props }: React.ComponentProps<typeof SelectPrimitive.ScrollDownButton>) {
  return (
    <SelectPrimitive.ScrollDownButton className={cn('flex items-center justify-center py-1', className)} {...props}>
      <ChevronDownIcon className="size-4" />
    </SelectPrimitive.ScrollDownButton>
  );
}

export const QuietSelectGroup = SelectPrimitive.Group;

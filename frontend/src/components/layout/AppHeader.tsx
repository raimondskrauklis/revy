// frontend/src/components/layout/AppHeader.tsx
import { Menu } from 'lucide-react';
import { WorkspaceSwitcher } from '@/components/layout/WorkspaceSwitcher';
import { UserMenu } from '@/components/layout/UserMenu';
import { useSidebar } from '@/components/layout/SidebarProvider';

export function AppHeader() {
  const { openMobile, triggerRef } = useSidebar();

  return (
    <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[color:var(--app-ring)] bg-[color:var(--app-surface)] px-4 py-2 md:hidden">
      <div className="flex items-center gap-2">
        <button
          ref={triggerRef}
          type="button"
          onClick={openMobile}
          className="inline-flex h-11 w-11 items-center justify-center rounded-[var(--app-radius-md)] text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" aria-hidden />
        </button>
        <WorkspaceSwitcher />
      </div>
      <UserMenu />
    </header>
  );
}
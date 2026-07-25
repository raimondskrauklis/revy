// frontend/src/components/layout/AppHeader.tsx
import { WorkspaceSwitcher } from '@/components/layout/WorkspaceSwitcher';
import { UserMenu } from '@/components/layout/UserMenu';

export function AppHeader() {
  return (
    <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[color:var(--app-ring)] bg-[color:var(--app-surface)] px-4 py-2 md:hidden">
      <WorkspaceSwitcher />
      <UserMenu />
    </header>
  );
}

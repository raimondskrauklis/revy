// frontend/src/components/layout/AppShellLayout.tsx
/**
 * App shell — sidebar nav + main Outlet.
 * KP equivalent: WorkspaceLayout + StandardSidebar.
 * See docs/frontend/patterns/LAYOUT_GUIDE.md and reference/ROUTING.md
 */
import { Outlet } from 'react-router-dom';
import { ImpersonationBanner } from '@/features/admin/components/ImpersonationBanner';
import { StackShell } from '@/components/layout/StackShell';
import { AppHeader } from '@/components/layout/AppHeader';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { MobileSidebarSheet } from '@/components/layout/MobileSidebarSheet';
import { MobileBottomNav } from '@/components/layout/MobileBottomNav';
import { SidebarProvider } from '@/components/layout/SidebarProvider';

export function AppShellLayout() {
  return (
    <SidebarProvider>
      <div className="flex h-screen min-h-0 overflow-hidden bg-[color:var(--app-canvas)]">
        <AppSidebar />
        <MobileSidebarSheet />

        <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <ImpersonationBanner />
          <AppHeader />
          <div data-scroll-lock-target className="flex-1 overflow-y-auto p-4 md:p-6 pb-16 md:pb-6">
            <div className="mx-auto max-w-[900px]">
              <Outlet />
            </div>
          </div>
          <MobileBottomNav />
        </main>
        <StackShell />
      </div>
    </SidebarProvider>
  );
}
// frontend/src/features/admin/layout/AdminLayout.tsx
import { Link, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { AdminSidebar } from '@/features/admin/layout/AdminSidebar';
import { UserMenu } from '@/components/layout/UserMenu';

export function AdminLayout() {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col bg-[color:var(--app-canvas)]">
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[color:var(--app-ring)] bg-[color:var(--app-surface)] px-4 py-3">
        <div className="flex items-center gap-3">
          <Link
            to="/dashboard"
            className="flex min-h-11 items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
            {t('admin.backToApp')}
          </Link>
          <span className="text-sm font-semibold text-[color:var(--app-text-strong)]">
            {t('admin.title')}
          </span>
        </div>
        <UserMenu />
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-6 p-4 md:flex-row md:p-6">
        <AdminSidebar />
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
